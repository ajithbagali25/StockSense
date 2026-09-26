from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import Delivery, User
from ...schemas.delivery import DeliveryCreate, DeliveryRead
from ...services.delivery_service import (
	InvalidDeliveryStateError,
	cancel_delivery,
	create_delivery,
	get_delivery,
	pack_delivery,
	pick_delivery,
	validate_delivery,
)


router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])


@router.get("", response_model=dict)
def list_deliveries(
	status_filter: str | None = Query(default=None, alias="status"),
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(Delivery).options(selectinload(Delivery.items))
	if status_filter:
		query = query.where(Delivery.status == status_filter.upper())
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	items = list(database.scalars(query.order_by(Delivery.created_at.desc()).offset((page - 1) * limit).limit(limit)))
	return {"items": [DeliveryRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=DeliveryRead, status_code=status.HTTP_201_CREATED)
def create_delivery_endpoint(payload: DeliveryCreate, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Delivery:
	try:
		delivery = create_delivery(database, payload, current_user.id)
		database.commit()
		return get_delivery(database, delivery.id)
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Delivery number already exists") from error
	except ValueError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{delivery_id}", response_model=DeliveryRead)
def get_delivery_endpoint(delivery_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Delivery:
	delivery = get_delivery(database, delivery_id)
	if delivery is None:
		raise HTTPException(status_code=404, detail="Delivery not found")
	return delivery


@router.post("/{delivery_id}/pick", response_model=DeliveryRead)
def pick_delivery_endpoint(delivery_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Delivery:
	delivery = get_delivery(database, delivery_id)
	if delivery is None:
		raise HTTPException(status_code=404, detail="Delivery not found")
	try:
		pick_delivery(delivery)
		database.commit()
		return get_delivery(database, delivery.id)
	except InvalidDeliveryStateError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{delivery_id}/pack", response_model=DeliveryRead)
def pack_delivery_endpoint(delivery_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Delivery:
	delivery = get_delivery(database, delivery_id)
	if delivery is None:
		raise HTTPException(status_code=404, detail="Delivery not found")
	try:
		pack_delivery(delivery)
		database.commit()
		return get_delivery(database, delivery.id)
	except (ValueError, InvalidDeliveryStateError) as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{delivery_id}/validate", response_model=DeliveryRead)
def validate_delivery_endpoint(delivery_id: int, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Delivery:
	delivery = get_delivery(database, delivery_id)
	if delivery is None:
		raise HTTPException(status_code=404, detail="Delivery not found")
	try:
		validate_delivery(database, delivery, current_user.id)
		database.commit()
		return get_delivery(database, delivery.id)
	except (ValueError, InvalidDeliveryStateError) as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{delivery_id}/cancel", response_model=DeliveryRead)
def cancel_delivery_endpoint(delivery_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Delivery:
	delivery = get_delivery(database, delivery_id)
	if delivery is None:
		raise HTTPException(status_code=404, detail="Delivery not found")
	try:
		cancel_delivery(delivery)
		database.commit()
		return get_delivery(database, delivery.id)
	except InvalidDeliveryStateError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error
