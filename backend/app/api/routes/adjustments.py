from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import Adjustment, User
from ...schemas.adjustment import AdjustmentCreate, AdjustmentRead
from ...services.adjustment_service import (
	InvalidAdjustmentStateError,
	cancel_adjustment,
	create_adjustment,
	get_adjustment,
	validate_adjustment,
)


router = APIRouter(prefix="/api/adjustments", tags=["adjustments"])


@router.get("", response_model=dict)
def list_adjustments(
	status_filter: str | None = Query(default=None, alias="status"),
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(Adjustment)
	if status_filter:
		query = query.where(Adjustment.status == status_filter.upper())
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	items = list(database.scalars(query.order_by(Adjustment.created_at.desc()).offset((page - 1) * limit).limit(limit)))
	return {"items": [AdjustmentRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=AdjustmentRead, status_code=status.HTTP_201_CREATED)
def create_adjustment_endpoint(payload: AdjustmentCreate, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Adjustment:
	try:
		adjustment = create_adjustment(database, payload, current_user.id)
		database.commit()
		database.refresh(adjustment)
		return adjustment
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Adjustment number already exists") from error
	except ValueError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{adjustment_id}", response_model=AdjustmentRead)
def get_adjustment_endpoint(adjustment_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Adjustment:
	adjustment = get_adjustment(database, adjustment_id)
	if adjustment is None:
		raise HTTPException(status_code=404, detail="Adjustment not found")
	return adjustment


@router.post("/{adjustment_id}/validate", response_model=AdjustmentRead)
def validate_adjustment_endpoint(adjustment_id: int, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Adjustment:
	adjustment = get_adjustment(database, adjustment_id)
	if adjustment is None:
		raise HTTPException(status_code=404, detail="Adjustment not found")
	try:
		validate_adjustment(database, adjustment, current_user.id)
		database.commit()
		database.refresh(adjustment)
		return adjustment
	except (ValueError, InvalidAdjustmentStateError) as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{adjustment_id}/cancel", response_model=AdjustmentRead)
def cancel_adjustment_endpoint(adjustment_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Adjustment:
	adjustment = get_adjustment(database, adjustment_id)
	if adjustment is None:
		raise HTTPException(status_code=404, detail="Adjustment not found")
	try:
		cancel_adjustment(adjustment)
		database.commit()
		database.refresh(adjustment)
		return adjustment
	except InvalidAdjustmentStateError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error
