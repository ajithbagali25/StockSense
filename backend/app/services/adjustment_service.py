from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Adjustment, Inventory, Location, Product, Warehouse
from ..schemas.adjustment import AdjustmentCreate
from ..utils.enums import DocumentStatus
from .inventory_service import adjust_stock


class InvalidAdjustmentStateError(ValueError):
	pass


def get_adjustment(database: Session, adjustment_id: int) -> Adjustment | None:
	return database.scalar(select(Adjustment).where(Adjustment.id == adjustment_id))


def create_adjustment(database: Session, payload: AdjustmentCreate, created_by: int) -> Adjustment:
	product = database.scalar(select(Product).where(Product.id == payload.product_id, Product.is_active.is_(True)))
	warehouse = database.scalar(select(Warehouse).where(Warehouse.id == payload.warehouse_id, Warehouse.is_active.is_(True)))
	location = database.scalar(select(Location).where(Location.id == payload.location_id, Location.warehouse_id == payload.warehouse_id, Location.is_active.is_(True)))
	if product is None:
		raise ValueError("Product not found or inactive")
	if warehouse is None or location is None:
		raise ValueError("Active warehouse and matching location are required")
	inventory = database.scalar(select(Inventory).where(Inventory.product_id == payload.product_id, Inventory.location_id == payload.location_id))
	system_quantity = inventory.quantity if inventory is not None else 0
	adjustment = Adjustment(
		adjustment_number=payload.adjustment_number,
		product_id=payload.product_id,
		warehouse_id=payload.warehouse_id,
		location_id=payload.location_id,
		system_quantity=system_quantity,
		counted_quantity=payload.counted_quantity,
		difference=payload.counted_quantity - system_quantity,
		reason=payload.reason,
		created_by=created_by,
	)
	database.add(adjustment)
	database.flush()
	return adjustment


def validate_adjustment(database: Session, adjustment: Adjustment, validated_by: int) -> Adjustment:
	if adjustment.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidAdjustmentStateError("Adjustment cannot be validated from its current state")
	current = database.scalar(
		select(Inventory)
		.where(Inventory.product_id == adjustment.product_id, Inventory.location_id == adjustment.location_id)
		.with_for_update()
	)
	current_quantity = current.quantity if current is not None else 0
	if current_quantity != adjustment.system_quantity:
		raise ValueError("Inventory changed since this adjustment was created")
	adjust_stock(
		database,
		product_id=adjustment.product_id,
		warehouse_id=adjustment.warehouse_id,
		location_id=adjustment.location_id,
		counted_quantity=adjustment.counted_quantity,
		performed_by=validated_by,
		reference_type="ADJUSTMENT",
		reference_id=adjustment.id,
		reason=adjustment.reason,
	)
	adjustment.status = DocumentStatus.DONE
	adjustment.validated_by = validated_by
	database.flush()
	return adjustment


def cancel_adjustment(adjustment: Adjustment) -> Adjustment:
	if adjustment.status in {DocumentStatus.DONE, DocumentStatus.CANCELED}:
		raise InvalidAdjustmentStateError("Adjustment cannot be canceled from its current state")
	adjustment.status = DocumentStatus.CANCELED
	return adjustment
