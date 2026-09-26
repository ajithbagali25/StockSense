from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, require_roles
from ...database.session import get_db
from ...models import User, Warehouse
from ...schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from ...services.product_service import list_warehouses
from ...utils.enums import UserRole


router = APIRouter(prefix="/api/warehouses", tags=["warehouses"])
write_roles = require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=dict)
def get_warehouses(
	search: str | None = None,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	items, total = list_warehouses(database, search, (page - 1) * limit, limit)
	return {"items": [WarehouseRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(payload: WarehouseCreate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Warehouse:
	warehouse = Warehouse(**payload.model_dump())
	database.add(warehouse)
	try:
		database.commit()
		database.refresh(warehouse)
		return warehouse
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Warehouse code already exists") from error


@router.get("/{warehouse_id}", response_model=WarehouseRead)
def get_warehouse(warehouse_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Warehouse:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == warehouse_id))
	if warehouse is None:
		raise HTTPException(status_code=404, detail="Warehouse not found")
	return warehouse


@router.put("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Warehouse:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == warehouse_id))
	if warehouse is None:
		raise HTTPException(status_code=404, detail="Warehouse not found")
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(warehouse, field, value)
	try:
		database.commit()
		database.refresh(warehouse)
		return warehouse
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Warehouse code already exists") from error


@router.delete("/{warehouse_id}", response_model=WarehouseRead)
def disable_warehouse(warehouse_id: int, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Warehouse:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == warehouse_id))
	if warehouse is None:
		raise HTTPException(status_code=404, detail="Warehouse not found")
	warehouse.is_active = False
	database.commit()
	database.refresh(warehouse)
	return warehouse
