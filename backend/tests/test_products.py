from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.main import app
from app.models import Category, Product


def test_product_creation_search_and_duplicate_sku():
	client = TestClient(app)
	token = client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Ik9fMFfn78U1ql7aDG7RVw"}).json()["access_token"]
	headers = {"Authorization": f"Bearer {token}"}
	suffix = uuid4().hex[:8]
	category = client.post("/api/categories", headers=headers, json={"name": f"Test Category {suffix}"})
	assert category.status_code == 201
	category_id = category.json()["id"]
	sku = f"TEST-{suffix}"
	product = client.post("/api/products", headers=headers, json={"name": "Test Product", "sku": sku, "category_id": category_id, "unit_of_measure": "units"})
	assert product.status_code == 201
	assert client.get("/api/products", headers=headers, params={"search": sku}).json()["total"] == 1
	assert client.post("/api/products", headers=headers, json={"name": "Duplicate", "sku": sku, "unit_of_measure": "units"}).status_code == 409
	database = SessionLocal()
	database.execute(delete(Product).where(Product.sku == sku))
	database.execute(delete(Category).where(Category.id == category_id))
	database.commit()
	database.close()
