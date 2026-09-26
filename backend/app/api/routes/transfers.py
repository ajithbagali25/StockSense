from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import Transfer, User
from ...schemas.transfer import TransferCreate, TransferRead
from ...services.transfer_service import (
	InvalidTransferStateError,
	cancel_transfer,
	complete_transfer,
	create_transfer,
	get_transfer,
)


router = APIRouter(prefix="/api/transfers", tags=["transfers"])


@router.get("", response_model=dict)
def list_transfers(
	status_filter: str | None = Query(default=None, alias="status"),
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	query = select(Transfer).options(selectinload(Transfer.items))
	if status_filter:
		query = query.where(Transfer.status == status_filter.upper())
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	items = list(database.scalars(query.order_by(Transfer.created_at.desc()).offset((page - 1) * limit).limit(limit)))
	return {"items": [TransferRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
def create_transfer_endpoint(payload: TransferCreate, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Transfer:
	try:
		transfer = create_transfer(database, payload, current_user.id)
		database.commit()
		return get_transfer(database, transfer.id)
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Transfer number already exists") from error
	except ValueError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/{transfer_id}", response_model=TransferRead)
def get_transfer_endpoint(transfer_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Transfer:
	transfer = get_transfer(database, transfer_id)
	if transfer is None:
		raise HTTPException(status_code=404, detail="Transfer not found")
	return transfer


@router.post("/{transfer_id}/complete", response_model=TransferRead)
def complete_transfer_endpoint(transfer_id: int, database: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Transfer:
	transfer = get_transfer(database, transfer_id)
	if transfer is None:
		raise HTTPException(status_code=404, detail="Transfer not found")
	try:
		complete_transfer(database, transfer, current_user.id)
		database.commit()
		return get_transfer(database, transfer.id)
	except (ValueError, InvalidTransferStateError) as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/{transfer_id}/cancel", response_model=TransferRead)
def cancel_transfer_endpoint(transfer_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Transfer:
	transfer = get_transfer(database, transfer_id)
	if transfer is None:
		raise HTTPException(status_code=404, detail="Transfer not found")
	try:
		cancel_transfer(transfer)
		database.commit()
		return get_transfer(database, transfer.id)
	except InvalidTransferStateError as error:
		database.rollback()
		raise HTTPException(status_code=400, detail=str(error)) from error
