from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models import Inventory, Location, Product, StockMovement, Warehouse
from app.services.inventory_service import increase_stock


def test_transfer_moves_stock_and_creates_paired_ledger_entries():
    client = TestClient(app)
    login = client.post(
        "/api/auth/login",
        json={"email": "manager@example.com", "password": "Ik9fMFfn78U1ql7aDG7RVw"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    database = SessionLocal()
    warehouse = database.scalar(select(Warehouse).where(Warehouse.code == "MAIN"))
    source_location = database.scalar(
        select(Location).where(Location.warehouse_id == warehouse.id, Location.code == "RACK-A")
    )
    destination_location = database.scalar(
        select(Location).where(Location.warehouse_id == warehouse.id, Location.code == "RACK-B")
    )
    product = Product(
        name="Phase 13 Transfer Product",
        sku=f"P13-{uuid4().hex[:8]}",
        unit_of_measure="units",
    )
    database.add(product)
    database.flush()
    user_id = database.scalar(select(__import__("app.models", fromlist=["User"]).User.id).where(__import__("app.models", fromlist=["User"]).User.email == "manager@example.com"))
    increase_stock(
        database,
        product_id=product.id,
        warehouse_id=warehouse.id,
        location_id=source_location.id,
        quantity=Decimal("100"),
        performed_by=user_id,
    )
    database.commit()
    transfer_id = None

    try:
        response = client.post(
            "/api/transfers",
            headers=headers,
            json={
                "transfer_number": f"T-{uuid4().hex[:8]}",
                "source_warehouse_id": warehouse.id,
                "source_location_id": source_location.id,
                "destination_warehouse_id": warehouse.id,
                "destination_location_id": destination_location.id,
                "items": [{"product_id": product.id, "quantity": 30}],
            },
        )
        assert response.status_code == 201, response.text
        transfer_id = response.json()["id"]

        response = client.post(f"/api/transfers/{transfer_id}/complete", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "DONE"

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
        movements = database.scalars(select(StockMovement).where(StockMovement.product_id == product.id)).all()
        assert source.quantity == Decimal("70")
        assert destination.quantity == Decimal("30")
        assert source.quantity + destination.quantity == Decimal("100")
        assert [movement.quantity for movement in movements] == [Decimal("100"), Decimal("-30"), Decimal("30")]

        invalid = client.post(
            "/api/transfers",
            headers=headers,
            json={
                "transfer_number": f"T-{uuid4().hex[:8]}",
                "source_warehouse_id": warehouse.id,
                "source_location_id": source_location.id,
                "destination_warehouse_id": warehouse.id,
                "destination_location_id": source_location.id,
                "items": [{"product_id": product.id, "quantity": 1}],
            },
        )
        assert invalid.status_code == 400

    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id == product.id))
        database.execute(delete(Inventory).where(Inventory.product_id == product.id))
        if transfer_id is not None:
            from app.models import TransferItem, Transfer
            database.execute(delete(TransferItem).where(TransferItem.transfer_id == transfer_id))
            database.execute(delete(Transfer).where(Transfer.id == transfer_id))
        database.delete(product)
        database.commit()
        database.close()
