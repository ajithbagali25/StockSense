from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database.session import SessionLocal
from app.main import app
from app.models import User


def test_registration_login_and_protected_profile():
	client = TestClient(app)
	email = f"auth-{uuid4().hex[:8]}@example.com"
	registration = client.post(
		"/api/auth/register",
		json={"full_name": "Auth Test User", "email": email, "password": "StrongPass!123"},
	)
	assert registration.status_code == 201
	login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass!123"})
	assert login.status_code == 200
	token = login.json()["access_token"]
	profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
	assert profile.status_code == 200
	assert profile.json()["email"] == email
	assert "password_hash" not in profile.json()
	assert client.post("/api/auth/login", json={"email": email, "password": "wrong"}).status_code == 401
	database = SessionLocal()
	database.execute(delete(User).where(User.email == email))
	database.commit()
	database.close()
