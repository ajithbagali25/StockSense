from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import StockMovement, User
from ...schemas.inventory import StockMovementRead
from ...utils.enums import MovementType


router = APIRouter(prefix="/api/stock-movements", tags=["stock-movements"])


@router.get("", response_model=dict)
def get_stock_movements(
	product_id: int | None = None,
	warehouse_id: int | None = None,
	location_id: int | None = None,
	movement_type: MovementType | None = None,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(StockMovement)
	if product_id is not None:
		query = query.where(StockMovement.product_id == product_id)
	if warehouse_id is not None:
		query = query.where(StockMovement.warehouse_id == warehouse_id)
	if location_id is not None:
		query = query.where(StockMovement.location_id == location_id)
	if movement_type is not None:
		query = query.where(StockMovement.movement_type == movement_type)
	items = list(database.scalars(query.order_by(StockMovement.created_at.desc()).offset((page - 1) * limit).limit(limit)))
	return {
		"items": [StockMovementRead.model_validate(item) for item in items],
		"page": page,
		"limit": limit,
	}
