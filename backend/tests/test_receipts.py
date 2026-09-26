from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models import Inventory, Location, Product, Receipt, ReceiptItem, StockMovement, Supplier, Warehouse


def test_receipt_validation_increases_stock_and_creates_ledger_entry():
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
    supplier = database.scalar(select(Supplier).where(Supplier.name == "ABC Metals"))
    product = Product(
        name="Phase 11 Receipt Product",
        sku=f"P11-{uuid4().hex[:8]}",
        unit_of_measure="units",
    )
    database.add(product)
    database.commit()
    database.refresh(product)
    receipt_id = None

    try:
        response = client.post(
            "/api/receipts",
            headers=headers,
            json={
                "receipt_number": f"R-{uuid4().hex[:8]}",
                "supplier_id": supplier.id,
                "warehouse_id": warehouse.id,
                "location_id": location.id,
                "items": [{"product_id": product.id, "quantity": 50}],
            },
        )
        assert response.status_code == 201, response.text
        receipt_id = response.json()["id"]

        response = client.post(f"/api/receipts/{receipt_id}/validate", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "DONE"

        inventory = database.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.location_id == location.id,
            )
        )
        movement = database.scalar(select(StockMovement).where(StockMovement.product_id == product.id))
        assert inventory.quantity == Decimal("50")
        assert movement.quantity == Decimal("50")

    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id == product.id))
        database.execute(delete(Inventory).where(Inventory.product_id == product.id))
        if receipt_id is not None:
            database.execute(delete(ReceiptItem).where(ReceiptItem.receipt_id == receipt_id))
            database.execute(delete(Receipt).where(Receipt.id == receipt_id))
        database.delete(product)
        database.commit()
        database.close()
