from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Adjustment, Category, Delivery, Inventory, Product, Receipt, Transfer
from ..utils.enums import DocumentStatus


def inventory_totals(database: Session, warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None):
	query = (
		select(Product.id, Product.name, Product.sku, Product.reorder_level, func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0).label("available_quantity"))
		.join(Inventory, Inventory.product_id == Product.id)
		.outerjoin(Category, Category.id == Product.category_id)
		.where(Product.is_active.is_(True))
		.group_by(Product.id, Product.name, Product.sku, Product.reorder_level)
	)
	if warehouse_id is not None:
		query = query.where(Inventory.warehouse_id == warehouse_id)
	if location_id is not None:
		query = query.where(Inventory.location_id == location_id)
	if category_id is not None:
		query = query.where(Product.category_id == category_id)
	return database.execute(query).all()


def low_stock(database: Session, warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None) -> list[dict]:
	return [
		{
			"product_id": row.id,
			"name": row.name,
			"sku": row.sku,
			"available_quantity": row.available_quantity,
			"reorder_level": row.reorder_level,
		}
		for row in inventory_totals(database, warehouse_id, location_id, category_id)
		if Decimal(str(row.available_quantity)) > 0 and row.available_quantity <= row.reorder_level
	]


def out_of_stock(database: Session, warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None) -> list[dict]:
	return [
		{
			"product_id": row.id,
			"name": row.name,
			"sku": row.sku,
			"available_quantity": row.available_quantity,
			"reorder_level": row.reorder_level,
		}
		for row in inventory_totals(database, warehouse_id, location_id, category_id)
		if row.available_quantity <= 0
	]


def pending_count(database: Session, model, warehouse_id: int | None = None, location_id: int | None = None) -> int:
	query = select(func.count()).select_from(model).where(model.status.not_in([DocumentStatus.DONE, DocumentStatus.CANCELED]))
	if hasattr(model, "warehouse_id") and warehouse_id is not None:
		query = query.where(model.warehouse_id == warehouse_id)
	if hasattr(model, "location_id") and location_id is not None:
		query = query.where(model.location_id == location_id)
	return database.scalar(query) or 0


def dashboard_summary(database: Session, warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None) -> dict:
	totals = inventory_totals(database, warehouse_id, location_id, category_id)
	return {
		"total_products_in_stock": sum(1 for row in totals if row.available_quantity > 0),
		"low_stock_items": len(low_stock(database, warehouse_id, location_id, category_id)),
		"out_of_stock_items": len(out_of_stock(database, warehouse_id, location_id, category_id)),
		"pending_receipts": pending_count(database, Receipt, warehouse_id, location_id),
		"pending_deliveries": pending_count(database, Delivery, warehouse_id, location_id),
		"scheduled_transfers": pending_count(database, Transfer),
		"pending_adjustments": pending_count(database, Adjustment, warehouse_id, location_id),
	}
