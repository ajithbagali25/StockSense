from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Location, Product, Transfer, TransferItem, Warehouse
from ..schemas.transfer import TransferCreate
from ..utils.enums import DocumentStatus
from .inventory_service import transfer_stock


class InvalidTransferStateError(ValueError):
	pass


def get_transfer(database: Session, transfer_id: int) -> Transfer | None:
	return database.scalar(
		select(Transfer).options(selectinload(Transfer.items)).where(Transfer.id == transfer_id)
	)


def validate_transfer_references(database: Session, payload: TransferCreate) -> None:
	if payload.source_location_id == payload.destination_location_id:
		raise ValueError("Source and destination locations must differ")
	source_warehouse = database.scalar(select(Warehouse).where(Warehouse.id == payload.source_warehouse_id, Warehouse.is_active.is_(True)))
	destination_warehouse = database.scalar(select(Warehouse).where(Warehouse.id == payload.destination_warehouse_id, Warehouse.is_active.is_(True)))
	source_location = database.scalar(select(Location).where(Location.id == payload.source_location_id, Location.warehouse_id == payload.source_warehouse_id, Location.is_active.is_(True)))
	destination_location = database.scalar(select(Location).where(Location.id == payload.destination_location_id, Location.warehouse_id == payload.destination_warehouse_id, Location.is_active.is_(True)))
	if not all((source_warehouse, destination_warehouse, source_location, destination_location)):
		raise ValueError("Active source and destination warehouses/locations are required")
	product_ids = [item.product_id for item in payload.items]
	products = database.scalars(select(Product.id).where(Product.id.in_(product_ids), Product.is_active.is_(True))).all()
	if len(products) != len(set(product_ids)):
		raise ValueError("One or more products are not found or inactive")


def create_transfer(database: Session, payload: TransferCreate, created_by: int) -> Transfer:
	validate_transfer_references(database, payload)
	transfer = Transfer(
		transfer_number=payload.transfer_number,
		source_warehouse_id=payload.source_warehouse_id,
		source_location_id=payload.source_location_id,
		destination_warehouse_id=payload.destination_warehouse_id,
		destination_location_id=payload.destination_location_id,
		scheduled_at=payload.scheduled_at,
		created_by=created_by,
	)
	transfer.items = [TransferItem(product_id=item.product_id, quantity=item.quantity) for item in payload.items]
	database.add(transfer)
	database.flush()
	return transfer


def complete_transfer(database: Session, transfer: Transfer, completed_by: int) -> Transfer:
	if transfer.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidTransferStateError("Transfer cannot be completed from its current state")
	for item in transfer.items:
		transfer_stock(
			database,
			product_id=item.product_id,
			source_warehouse_id=transfer.source_warehouse_id,
			source_location_id=transfer.source_location_id,
			destination_warehouse_id=transfer.destination_warehouse_id,
			destination_location_id=transfer.destination_location_id,
			quantity=item.quantity,
			performed_by=completed_by,
			reference_type="TRANSFER",
			reference_id=transfer.id,
			reason=f"Transfer {transfer.transfer_number}",
		)
	transfer.status = DocumentStatus.DONE
	transfer.completed_at = datetime.now(timezone.utc)
	database.flush()
	return transfer


def cancel_transfer(transfer: Transfer) -> Transfer:
	if transfer.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidTransferStateError("Transfer cannot be canceled from its current state")
	transfer.status = DocumentStatus.CANCELED
	return transfer
