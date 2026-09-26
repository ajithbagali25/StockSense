from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, require_roles
from ...database.session import get_db
from ...models import Location, User, Warehouse
from ...schemas.location import LocationCreate, LocationRead, LocationUpdate
from ...services.product_service import list_locations
from ...utils.enums import UserRole


router = APIRouter(prefix="/api/locations", tags=["locations"])
write_roles = require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=dict)
def get_locations(
	warehouse_id: int | None = None,
	search: str | None = None,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	items, total = list_locations(database, warehouse_id, search, (page - 1) * limit, limit)
	return {"items": [LocationRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Location:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == payload.warehouse_id, Warehouse.is_active.is_(True)))
	if warehouse is None:
		raise HTTPException(status_code=404, detail="Active warehouse not found")
	location = Location(**payload.model_dump())
	database.add(location)
	try:
		database.commit()
		database.refresh(location)
		return location
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Location code already exists in this warehouse") from error


@router.put("/{location_id}", response_model=LocationRead)
def update_location(location_id: int, payload: LocationUpdate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Location:
	location = database.scalar(select(Location).where(Location.id == location_id))
	if location is None:
		raise HTTPException(status_code=404, detail="Location not found")
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(location, field, value)
	try:
		database.commit()
		database.refresh(location)
		return location
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Location code already exists in this warehouse") from error


@router.delete("/{location_id}", response_model=LocationRead)
def disable_location(location_id: int, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Location:
	location = database.scalar(select(Location).where(Location.id == location_id))
	if location is None:
		raise HTTPException(status_code=404, detail="Location not found")
	location.is_active = False
	database.commit()
	database.refresh(location)
	return location
