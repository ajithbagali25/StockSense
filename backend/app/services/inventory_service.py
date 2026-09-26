from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Inventory, StockMovement
from ..utils.enums import MovementType


class InsufficientStockError(ValueError):
	pass


class InventoryLocationError(ValueError):
	pass


def get_or_create_inventory(
	database: Session,
	product_id: int,
	warehouse_id: int,
	location_id: int,
	*,
	lock: bool = True,
) -> Inventory:
	query = select(Inventory).where(
		Inventory.product_id == product_id,
		Inventory.location_id == location_id,
	)
	if lock:
		query = query.with_for_update()
	inventory = database.scalar(query)
	if inventory is None:
		inventory = Inventory(
			product_id=product_id,
			warehouse_id=warehouse_id,
			location_id=location_id,
			quantity=Decimal("0"),
			reserved_quantity=Decimal("0"),
		)
		database.add(inventory)
		database.flush()
	elif inventory.warehouse_id != warehouse_id:
		raise InventoryLocationError("Inventory warehouse does not match location")
	return inventory


def create_stock_movement(
	database: Session,
	*,
	inventory: Inventory,
	movement_type: MovementType,
	quantity: Decimal,
	performed_by: int,
	reference_type: str | None = None,
	reference_id: int | None = None,
	reason: str | None = None,
) -> StockMovement:
	movement = StockMovement(
		product_id=inventory.product_id,
		warehouse_id=inventory.warehouse_id,
		location_id=inventory.location_id,
		movement_type=movement_type,
		quantity=quantity,
		quantity_before=inventory.quantity - quantity if quantity < 0 else inventory.quantity,
		quantity_after=inventory.quantity,
		reference_type=reference_type,
		reference_id=reference_id,
		reason=reason,
		performed_by=performed_by,
	)
	database.add(movement)
	return movement


def increase_stock(
	database: Session,
	*,
	product_id: int,
	warehouse_id: int,
	location_id: int,
	quantity: Decimal,
	performed_by: int,
	movement_type: MovementType = MovementType.RECEIPT,
	reference_type: str | None = None,
	reference_id: int | None = None,
	reason: str | None = None,
) -> Inventory:
	if quantity <= 0:
		raise ValueError("Quantity must be greater than zero")
	inventory = get_or_create_inventory(database, product_id, warehouse_id, location_id)
	before = inventory.quantity
	inventory.quantity += quantity
	movement = StockMovement(
		product_id=product_id,
		warehouse_id=warehouse_id,
		location_id=location_id,
		movement_type=movement_type,
		quantity=quantity,
		quantity_before=before,
		quantity_after=inventory.quantity,
		reference_type=reference_type,
		reference_id=reference_id,
		reason=reason,
		performed_by=performed_by,
	)
	database.add(movement)
	database.flush()
	return inventory


def decrease_stock(
	database: Session,
	*,
	product_id: int,
	warehouse_id: int,
	location_id: int,
	quantity: Decimal,
	performed_by: int,
	movement_type: MovementType = MovementType.DELIVERY,
	reference_type: str | None = None,
	reference_id: int | None = None,
	reason: str | None = None,
) -> Inventory:
	if quantity <= 0:
		raise ValueError("Quantity must be greater than zero")
	inventory = get_or_create_inventory(database, product_id, warehouse_id, location_id)
	available = inventory.quantity - inventory.reserved_quantity
	if available < quantity:
		raise InsufficientStockError("Insufficient available stock")
	before = inventory.quantity
	inventory.quantity -= quantity
	movement = StockMovement(
		product_id=product_id,
		warehouse_id=warehouse_id,
		location_id=location_id,
		movement_type=movement_type,
		quantity=-quantity,
		quantity_before=before,
		quantity_after=inventory.quantity,
		reference_type=reference_type,
		reference_id=reference_id,
		reason=reason,
		performed_by=performed_by,
	)
	database.add(movement)
	database.flush()
	return inventory


def transfer_stock(
	database: Session,
	*,
	product_id: int,
	source_warehouse_id: int,
	source_location_id: int,
	destination_warehouse_id: int,
	destination_location_id: int,
	quantity: Decimal,
	performed_by: int,
	reference_type: str | None = None,
	reference_id: int | None = None,
	reason: str | None = None,
) -> tuple[Inventory, Inventory]:
	if source_location_id == destination_location_id:
		raise ValueError("Source and destination locations must differ")
	source = decrease_stock(
		database,
		product_id=product_id,
		warehouse_id=source_warehouse_id,
		location_id=source_location_id,
		quantity=quantity,
		performed_by=performed_by,
		movement_type=MovementType.TRANSFER_OUT,
		reference_type=reference_type,
		reference_id=reference_id,
		reason=reason,
	)
	destination = increase_stock(
		database,
		product_id=product_id,
		warehouse_id=destination_warehouse_id,
		location_id=destination_location_id,
		quantity=quantity,
		performed_by=performed_by,
		movement_type=MovementType.TRANSFER_IN,
		reference_type=reference_type,
		reference_id=reference_id,
		reason=reason,
	)
	return source, destination


def adjust_stock(
	database: Session,
	*,
	product_id: int,
	warehouse_id: int,
	location_id: int,
	counted_quantity: Decimal,
	performed_by: int,
	reference_type: str | None = None,
	reference_id: int | None = None,
	reason: str | None = None,
) -> Inventory:
	if counted_quantity < 0:
		raise ValueError("Counted quantity cannot be negative")
	inventory = get_or_create_inventory(database, product_id, warehouse_id, location_id)
	difference = counted_quantity - inventory.quantity
	if difference == 0:
		return inventory
	before = inventory.quantity
	inventory.quantity = counted_quantity
	database.add(
		StockMovement(
			product_id=product_id,
			warehouse_id=warehouse_id,
			location_id=location_id,
			movement_type=MovementType.ADJUSTMENT_IN if difference > 0 else MovementType.ADJUSTMENT_OUT,
			quantity=difference,
			quantity_before=before,
			quantity_after=counted_quantity,
			reference_type=reference_type,
			reference_id=reference_id,
			reason=reason,
			performed_by=performed_by,
		)
	)
	database.flush()
	return inventory


def get_current_stock(database: Session, product_id: int, warehouse_id: int | None = None, location_id: int | None = None) -> list[Inventory]:
	query = select(Inventory).where(Inventory.product_id == product_id)
	if warehouse_id is not None:
		query = query.where(Inventory.warehouse_id == warehouse_id)
	if location_id is not None:
		query = query.where(Inventory.location_id == location_id)
	return list(database.scalars(query.order_by(Inventory.location_id)))


def get_available_stock(inventory: Inventory) -> Decimal:
	return inventory.quantity - inventory.reserved_quantity


def check_stock_availability(database: Session, product_id: int, location_id: int, quantity: Decimal) -> bool:
	inventory = database.scalar(select(Inventory).where(Inventory.product_id == product_id, Inventory.location_id == location_id))
	return inventory is not None and get_available_stock(inventory) >= quantity
