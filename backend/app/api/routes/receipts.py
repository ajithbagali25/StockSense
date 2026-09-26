from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import Receipt, User
from ...schemas.receipt import ReceiptCreate, ReceiptRead, ReceiptUpdate
from ...services.receipt_service import (
	InvalidReceiptStateError,
	cancel_receipt,
	create_receipt,
	get_receipt,
	update_receipt,
	validate_receipt,
)


router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.get("", response_model=dict)
def list_receipts(
	status_filter: str | None = Query(default=None, alias="status"),
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(Receipt).options(selectinload(Receipt.items))
	if status_filter:
		query = query.where(Receipt.status == status_filter.upper())
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	items = list(database.scalars(query.order_by(Receipt.created_at.desc()).offset((page - 1) * limit).limit(limit)))
	return {"items": [ReceiptRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
def create_receipt_endpoint(payload: ReceiptCreate, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Receipt:
	try:
		receipt = create_receipt(database, payload, current_user.id)
		database.commit()
		database.refresh(receipt)
		return get_receipt(database, receipt.id)
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Receipt number already exists") from error
	except ValueError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{receipt_id}", response_model=ReceiptRead)
def get_receipt_endpoint(receipt_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Receipt:
	receipt = get_receipt(database, receipt_id)
	if receipt is None:
		raise HTTPException(status_code=404, detail="Receipt not found")
	return receipt


@router.put("/{receipt_id}", response_model=ReceiptRead)
def update_receipt_endpoint(receipt_id: int, payload: ReceiptUpdate, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Receipt:
	receipt = get_receipt(database, receipt_id)
	if receipt is None:
		raise HTTPException(status_code=404, detail="Receipt not found")
	try:
		receipt = update_receipt(database, receipt, payload)
		database.commit()
		return get_receipt(database, receipt.id)
	except ValueError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{receipt_id}/validate", response_model=ReceiptRead)
def validate_receipt_endpoint(receipt_id: int, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Receipt:
	receipt = get_receipt(database, receipt_id)
	if receipt is None:
		raise HTTPException(status_code=404, detail="Receipt not found")
	try:
		receipt = validate_receipt(database, receipt, current_user.id)
		database.commit()
		return get_receipt(database, receipt.id)
	except (ValueError, InvalidReceiptStateError) as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{receipt_id}/cancel", response_model=ReceiptRead)
def cancel_receipt_endpoint(receipt_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Receipt:
	receipt = get_receipt(database, receipt_id)
	if receipt is None:
		raise HTTPException(status_code=404, detail="Receipt not found")
	try:
		receipt = cancel_receipt(receipt)
		database.commit()
		return get_receipt(database, receipt.id)
	except InvalidReceiptStateError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error
