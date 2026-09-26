from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import Inventory, User
from ...schemas.inventory import InventoryRead


router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def serialize_inventory(item: Inventory) -> InventoryRead:
	return InventoryRead(
		id=item.id,
		product_id=item.product_id,
		warehouse_id=item.warehouse_id,
		location_id=item.location_id,
		quantity=item.quantity,
		reserved_quantity=item.reserved_quantity,
		available_quantity=item.quantity - item.reserved_quantity,
	)


@router.get("", response_model=dict)
def get_inventory(
	product_id: int | None = None,
	warehouse_id: int | None = None,
	location_id: int | None = None,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(Inventory)
	if product_id is not None:
		query = query.where(Inventory.product_id == product_id)
	if warehouse_id is not None:
		query = query.where(Inventory.warehouse_id == warehouse_id)
	if location_id is not None:
		query = query.where(Inventory.location_id == location_id)
	items = list(database.scalars(query.order_by(Inventory.id).offset((page - 1) * limit).limit(limit)))
	return {"items": [serialize_inventory(item) for item in items], "page": page, "limit": limit}


@router.get("/product/{product_id}", response_model=list[InventoryRead])
def get_product_inventory(product_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[InventoryRead]:
	return [serialize_inventory(item) for item in database.scalars(select(Inventory).where(Inventory.product_id == product_id))]


@router.get("/warehouse/{warehouse_id}", response_model=list[InventoryRead])
def get_warehouse_inventory(warehouse_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[InventoryRead]:
	return [serialize_inventory(item) for item in database.scalars(select(Inventory).where(Inventory.warehouse_id == warehouse_id))]


@router.get("/location/{location_id}", response_model=list[InventoryRead])
def get_location_inventory(location_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[InventoryRead]:
	return [serialize_inventory(item) for item in database.scalars(select(Inventory).where(Inventory.location_id == location_id))]
