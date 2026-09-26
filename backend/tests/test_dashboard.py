from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models import Inventory, Location, Product, StockMovement, Warehouse
from app.services.inventory_service import increase_stock


def test_dashboard_summary_and_stock_alerts_use_database_inventory():
    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"email": "manager@example.com", "password": "Ik9fMFfn78U1ql7aDG7RVw"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    database = SessionLocal()
    warehouse = database.scalar(select(Warehouse).where(Warehouse.code == "MAIN"))
    location = database.scalar(
        select(Location).where(Location.warehouse_id == warehouse.id, Location.code == "RACK-B")
    )
    low_product = Product(
        name="Phase 15 Low Product",
        sku=f"P15L-{uuid4().hex[:8]}",
        unit_of_measure="units",
        reorder_level=5,
    )
    out_product = Product(
        name="Phase 15 Out Product",
        sku=f"P15O-{uuid4().hex[:8]}",
        unit_of_measure="units",
        reorder_level=5,
    )
    database.add_all([low_product, out_product])
    database.flush()
    user_id = database.scalar(select(__import__("app.models", fromlist=["User"]).User.id).where(__import__("app.models", fromlist=["User"]).User.email == "manager@example.com"))
    increase_stock(
        database,
        product_id=low_product.id,
        warehouse_id=warehouse.id,
        location_id=location.id,
        quantity=Decimal("2"),
        performed_by=user_id,
    )
    database.add(
        Inventory(
            product_id=out_product.id,
            warehouse_id=warehouse.id,
            location_id=location.id,
            quantity=0,
            reserved_quantity=0,
        )
    )
    database.commit()

    try:
        summary = client.get("/api/dashboard/summary", headers=headers, params={"warehouse_id": warehouse.id})
        assert summary.status_code == 200, summary.text
        assert summary.json()["low_stock_items"] >= 1
        assert summary.json()["out_of_stock_items"] >= 1
        low = client.get("/api/dashboard/low-stock", headers=headers, params={"warehouse_id": warehouse.id})
        out = client.get("/api/dashboard/out-of-stock", headers=headers, params={"warehouse_id": warehouse.id})
        assert any(item["product_id"] == low_product.id for item in low.json())
        assert any(item["product_id"] == out_product.id for item in out.json())

    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id.in_([low_product.id, out_product.id])))
        database.execute(delete(Inventory).where(Inventory.product_id.in_([low_product.id, out_product.id])))
        database.delete(low_product)
        database.delete(out_product)
        database.commit()
        database.close()
