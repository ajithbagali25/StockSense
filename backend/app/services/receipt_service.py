from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Location, Product, Receipt, ReceiptItem, Supplier, Warehouse
from ..schemas.receipt import ReceiptCreate, ReceiptUpdate
from ..utils.enums import DocumentStatus, MovementType
from .inventory_service import increase_stock


class InvalidReceiptStateError(ValueError):
	pass


def get_receipt(database: Session, receipt_id: int) -> Receipt | None:
	return database.scalar(
		select(Receipt).options(selectinload(Receipt.items)).where(Receipt.id == receipt_id)
	)


def validate_receipt_references(database: Session, warehouse_id: int, location_id: int, supplier_id: int | None, product_ids: list[int]) -> None:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.is_active.is_(True)))
	location = database.scalar(select(Location).where(Location.id == location_id, Location.warehouse_id == warehouse_id, Location.is_active.is_(True)))
	if warehouse is None or location is None:
		raise ValueError("Active warehouse and matching location are required")
	if supplier_id is not None and database.scalar(select(Supplier).where(Supplier.id == supplier_id)) is None:
		raise ValueError("Supplier not found")
	products = database.scalars(select(Product.id).where(Product.id.in_(product_ids), Product.is_active.is_(True))).all()
	if len(products) != len(set(product_ids)):
		raise ValueError("One or more products are not found or inactive")


def create_receipt(database: Session, payload: ReceiptCreate, created_by: int) -> Receipt:
	validate_receipt_references(
		database,
		payload.warehouse_id,
		payload.location_id,
		payload.supplier_id,
		[item.product_id for item in payload.items],
	)
	receipt = Receipt(
		receipt_number=payload.receipt_number,
		supplier_id=payload.supplier_id,
		warehouse_id=payload.warehouse_id,
		location_id=payload.location_id,
		created_by=created_by,
	)
	receipt.items = [ReceiptItem(product_id=item.product_id, quantity=item.quantity) for item in payload.items]
	database.add(receipt)
	database.flush()
	return receipt


def update_receipt(database: Session, receipt: Receipt, payload: ReceiptUpdate) -> Receipt:
	if receipt.status not in {DocumentStatus.DRAFT, DocumentStatus.WAITING, DocumentStatus.READY}:
		raise InvalidReceiptStateError("Only open receipts can be updated")
	values = payload.model_dump(exclude_unset=True)
	items = values.pop("items", None)
	warehouse_id = values.get("warehouse_id", receipt.warehouse_id)
	location_id = values.get("location_id", receipt.location_id)
	supplier_id = values.get("supplier_id", receipt.supplier_id)
	if items is not None:
		validate_receipt_references(database, warehouse_id, location_id, supplier_id, [item["product_id"] for item in items])
		receipt.items.clear()
		receipt.items.extend(ReceiptItem(product_id=item["product_id"], quantity=item["quantity"]) for item in items)
	for field, value in values.items():
		setattr(receipt, field, value)
	database.flush()
	return receipt


def validate_receipt(database: Session, receipt: Receipt, validated_by: int) -> Receipt:
	if receipt.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidReceiptStateError("Receipt cannot be validated from its current state")
	if not receipt.items:
		raise ValueError("Receipt must contain at least one item")
	for item in receipt.items:
		increase_stock(
			database,
			product_id=item.product_id,
			warehouse_id=receipt.warehouse_id,
			location_id=receipt.location_id,
			quantity=item.quantity,
			performed_by=validated_by,
			movement_type=MovementType.RECEIPT,
			reference_type="RECEIPT",
			reference_id=receipt.id,
			reason=f"Receipt {receipt.receipt_number}",
		)
	receipt.status = DocumentStatus.DONE
	receipt.validated_by = validated_by
	receipt.received_at = datetime.now(timezone.utc)
	database.flush()
	return receipt


def cancel_receipt(receipt: Receipt) -> Receipt:
	if receipt.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidReceiptStateError("Receipt cannot be canceled from its current state")
	receipt.status = DocumentStatus.CANCELED
	return receipt
