from decimal import Decimal

import pytest
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.models import Inventory, Location, Product, StockMovement, User, Warehouse
from app.services.inventory_service import (
    InsufficientStockError,
    adjust_stock,
    decrease_stock,
    increase_stock,
    transfer_stock,
)


def test_inventory_operations_create_ledger_and_prevent_negative_stock():
    database = SessionLocal()
    warehouse = Warehouse(name="Phase 9 Test Warehouse", code="P9-TEST")
    database.add(warehouse)
    database.flush()
    source_location = Location(warehouse_id=warehouse.id, name="Source", code="SRC")
    destination_location = Location(warehouse_id=warehouse.id, name="Destination", code="DST")
    database.add_all([source_location, destination_location])
    database.flush()
    product = Product(
        name="Phase 9 Test Product",
        sku="P9-TEST",
        unit_of_measure="units",
        reorder_level=Decimal("5"),
        reorder_quantity=Decimal("10"),
    )
    database.add(product)
    database.flush()
    user_id = database.scalar(select(User.id).where(User.email == "manager@example.com"))
    database.commit()

    try:
        increase_stock(
            database,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=source_location.id,
            quantity=Decimal("100"),
            performed_by=user_id,
        )
        decrease_stock(
            database,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=source_location.id,
            quantity=Decimal("20"),
            performed_by=user_id,
        )
        transfer_stock(
            database,
            product_id=product.id,
            source_warehouse_id=warehouse.id,
            source_location_id=source_location.id,
            destination_warehouse_id=warehouse.id,
            destination_location_id=destination_location.id,
            quantity=Decimal("20"),
            performed_by=user_id,
        )
        decrease_stock(
            database,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=destination_location.id,
            quantity=Decimal("10"),
            performed_by=user_id,
        )
        adjust_stock(
            database,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=destination_location.id,
            counted_quantity=Decimal("7"),
            performed_by=user_id,
            reason="Physical count",
        )
        database.commit()

        source = database.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.location_id == source_location.id,
            )
        )
        destination = database.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.location_id == destination_location.id,
            )
        )
        movements = database.scalars(
            select(StockMovement).where(StockMovement.product_id == product.id)
        ).all()
        assert source.quantity == Decimal("60")
        assert destination.quantity == Decimal("7")
        assert len(movements) == 6

        with pytest.raises(InsufficientStockError):
            decrease_stock(
                database,
                product_id=product.id,
                warehouse_id=warehouse.id,
                location_id=destination_location.id,
                quantity=Decimal("8"),
                performed_by=user_id,
            )
        database.rollback()
    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id == product.id))
        database.execute(delete(Inventory).where(Inventory.product_id == product.id))
        database.delete(product)
        database.delete(source_location)
        database.delete(destination_location)
        database.delete(warehouse)
        database.commit()
        database.close()
