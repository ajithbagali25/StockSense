from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Customer, Delivery, DeliveryItem, Location, Product, Warehouse
from ..schemas.delivery import DeliveryCreate
from ..utils.enums import DocumentStatus, MovementType
from .inventory_service import decrease_stock


class InvalidDeliveryStateError(ValueError):
	pass


def get_delivery(database: Session, delivery_id: int) -> Delivery | None:
	return database.scalar(
		select(Delivery).options(selectinload(Delivery.items)).where(Delivery.id == delivery_id)
	)


def validate_delivery_references(database: Session, payload: DeliveryCreate) -> None:
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == payload.warehouse_id, Warehouse.is_active.is_(True)))
	location = database.scalar(select(Location).where(Location.id == payload.location_id, Location.warehouse_id == payload.warehouse_id, Location.is_active.is_(True)))
	if warehouse is None or location is None:
		raise ValueError("Active warehouse and matching location are required")
	if payload.customer_id is not None and database.scalar(select(Customer).where(Customer.id == payload.customer_id)) is None:
		raise ValueError("Customer not found")
	product_ids = [item.product_id for item in payload.items]
	products = database.scalars(select(Product.id).where(Product.id.in_(product_ids), Product.is_active.is_(True))).all()
	if len(products) != len(set(product_ids)):
		raise ValueError("One or more products are not found or inactive")


def create_delivery(database: Session, payload: DeliveryCreate, created_by: int) -> Delivery:
	validate_delivery_references(database, payload)
	delivery = Delivery(
		delivery_number=payload.delivery_number,
		customer_id=payload.customer_id,
		warehouse_id=payload.warehouse_id,
		location_id=payload.location_id,
		scheduled_at=payload.scheduled_at,
		created_by=created_by,
	)
	delivery.items = [DeliveryItem(product_id=item.product_id, quantity=item.quantity) for item in payload.items]
	database.add(delivery)
	database.flush()
	return delivery


def pick_delivery(delivery: Delivery) -> Delivery:
	if delivery.status not in {DocumentStatus.DRAFT, DocumentStatus.WAITING}:
		raise InvalidDeliveryStateError("Delivery cannot be picked from its current state")
	for item in delivery.items:
		item.picked_quantity = item.quantity
	delivery.status = DocumentStatus.WAITING
	return delivery


def pack_delivery(delivery: Delivery) -> Delivery:
	if delivery.status != DocumentStatus.WAITING:
		raise InvalidDeliveryStateError("Delivery must be picked before packing")
	for item in delivery.items:
		if item.picked_quantity < item.quantity:
			raise ValueError("All delivery items must be picked")
		item.packed_quantity = item.quantity
	delivery.status = DocumentStatus.READY
	return delivery


def validate_delivery(database: Session, delivery: Delivery, validated_by: int) -> Delivery:
	if delivery.status != DocumentStatus.READY:
		raise InvalidDeliveryStateError("Delivery must be packed before validation")
	for item in delivery.items:
		if item.packed_quantity < item.quantity:
			raise ValueError("All delivery items must be packed")
		decrease_stock(
			database,
			product_id=item.product_id,
			warehouse_id=delivery.warehouse_id,
			location_id=delivery.location_id,
			quantity=item.quantity,
			performed_by=validated_by,
			movement_type=MovementType.DELIVERY,
			reference_type="DELIVERY",
			reference_id=delivery.id,
			reason=f"Delivery {delivery.delivery_number}",
		)
	delivery.status = DocumentStatus.DONE
	delivery.validated_by = validated_by
	delivery.delivered_at = datetime.now(timezone.utc)
	database.flush()
	return delivery


def cancel_delivery(delivery: Delivery) -> Delivery:
	if delivery.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidDeliveryStateError("Delivery cannot be canceled from its current state")
	delivery.status = DocumentStatus.CANCELED
	return delivery
