from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models import Adjustment, Inventory, Location, Product, StockMovement, Warehouse
from app.services.inventory_service import increase_stock


def test_adjustment_sets_counted_stock_and_creates_ledger_entry():
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
        select(Location).where(Location.warehouse_id == warehouse.id, Location.code == "RACK-A")
    )
    product = Product(
        name="Phase 14 Adjustment Product",
        sku=f"P14-{uuid4().hex[:8]}",
        unit_of_measure="units",
    )
    database.add(product)
    database.flush()
    user_id = database.scalar(select(__import__("app.models", fromlist=["User"]).User.id).where(__import__("app.models", fromlist=["User"]).User.email == "manager@example.com"))
    increase_stock(
        database,
        product_id=product.id,
        warehouse_id=warehouse.id,
        location_id=location.id,
        quantity=Decimal("100"),
        performed_by=user_id,
    )
    database.commit()
    adjustment_ids = []

    try:
        response = client.post(
            "/api/adjustments",
            headers=headers,
            json={
                "adjustment_number": f"A-{uuid4().hex[:8]}",
                "product_id": product.id,
                "warehouse_id": warehouse.id,
                "location_id": location.id,
                "counted_quantity": 97,
                "reason": "Physical count",
            },
        )
        assert response.status_code == 201, response.text
        adjustment_id = response.json()["id"]
        adjustment_ids.append(adjustment_id)
        assert response.json()["system_quantity"] == "100.000"
        assert response.json()["difference"] == "-3.000"

        response = client.post(f"/api/adjustments/{adjustment_id}/validate", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "DONE"

        inventory = database.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.location_id == location.id,
            )
        )
        movements = database.scalars(select(StockMovement).where(StockMovement.product_id == product.id)).all()
        assert inventory.quantity == Decimal("97")
        assert movements[-1].quantity == Decimal("-3")

        response = client.post(
            "/api/adjustments",
            headers=headers,
            json={
                "adjustment_number": f"A-{uuid4().hex[:8]}",
                "product_id": product.id,
                "warehouse_id": warehouse.id,
                "location_id": location.id,
                "counted_quantity": 90,
                "reason": "Second count",
            },
        )
        assert response.status_code == 201, response.text
        stale_id = response.json()["id"]
        adjustment_ids.append(stale_id)
        increase_stock(
            database,
            product_id=product.id,
            warehouse_id=warehouse.id,
            location_id=location.id,
            quantity=Decimal("1"),
            performed_by=user_id,
        )
        database.commit()
        assert client.post(f"/api/adjustments/{stale_id}/validate", headers=headers).status_code == 400

    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id == product.id))
        database.execute(delete(Inventory).where(Inventory.product_id == product.id))
        for adjustment_id in adjustment_ids:
            database.execute(delete(Adjustment).where(Adjustment.id == adjustment_id))
        database.delete(product)
        database.commit()
        database.close()
