from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.main import app
from app.models import Delivery, DeliveryItem, Inventory, Location, Product, StockMovement, Warehouse
from app.services.inventory_service import increase_stock


def test_delivery_pick_pack_validate_decreases_stock_and_blocks_insufficient_stock():
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
    product = Product(
        name="Phase 12 Delivery Product",
        sku=f"P12-{uuid4().hex[:8]}",
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
        quantity=Decimal("50"),
        performed_by=user_id,
    )
    database.commit()
    delivery_ids = []

    try:
        response = client.post(
            "/api/deliveries",
            headers=headers,
            json={
                "delivery_number": f"D-{uuid4().hex[:8]}",
                "warehouse_id": warehouse.id,
                "location_id": location.id,
                "items": [{"product_id": product.id, "quantity": 20}],
            },
        )
        assert response.status_code == 201, response.text
        delivery_id = response.json()["id"]
        delivery_ids.append(delivery_id)

        assert client.post(f"/api/deliveries/{delivery_id}/validate", headers=headers).status_code == 400
        assert client.post(f"/api/deliveries/{delivery_id}/pick", headers=headers).json()["status"] == "WAITING"
        assert client.post(f"/api/deliveries/{delivery_id}/pack", headers=headers).json()["status"] == "READY"
        assert client.post(f"/api/deliveries/{delivery_id}/validate", headers=headers).json()["status"] == "DONE"

        inventory = database.scalar(
            select(Inventory).where(
                Inventory.product_id == product.id,
                Inventory.location_id == location.id,
            )
        )
        deliveries = database.scalars(select(StockMovement).where(StockMovement.product_id == product.id)).all()
        assert inventory.quantity == Decimal("30")
        assert len(deliveries) == 2
        assert deliveries[-1].quantity == Decimal("-20")

        response = client.post(
            "/api/deliveries",
            headers=headers,
            json={
                "delivery_number": f"D-{uuid4().hex[:8]}",
                "warehouse_id": warehouse.id,
                "location_id": location.id,
                "items": [{"product_id": product.id, "quantity": 40}],
            },
        )
        assert response.status_code == 201, response.text
        insufficient_id = response.json()["id"]
        delivery_ids.append(insufficient_id)
        client.post(f"/api/deliveries/{insufficient_id}/pick", headers=headers)
        client.post(f"/api/deliveries/{insufficient_id}/pack", headers=headers)
        assert client.post(f"/api/deliveries/{insufficient_id}/validate", headers=headers).status_code == 400

    finally:
        database.execute(delete(StockMovement).where(StockMovement.product_id == product.id))
        database.execute(delete(Inventory).where(Inventory.product_id == product.id))
        for delivery_id in delivery_ids:
            database.execute(delete(DeliveryItem).where(DeliveryItem.delivery_id == delivery_id))
            database.execute(delete(Delivery).where(Delivery.id == delivery_id))
        database.delete(product)
        database.commit()
        database.close()
