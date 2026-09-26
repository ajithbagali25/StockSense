from decimal import Decimal
import os
from secrets import token_urlsafe

from pwdlib import PasswordHash
from sqlalchemy import select

from app.database.session import SessionLocal
from app.models import (
	Category,
	Customer,
	Inventory,
	Location,
	Product,
	StockMovement,
	Supplier,
	User,
	Warehouse,
)
from app.utils.enums import MovementType, UserRole


password_hasher = PasswordHash.recommended()


def seed_password(name: str) -> str:
	password = os.getenv(name)
	if password:
		return password
	return token_urlsafe(16)


def get_or_create(session, model, lookup: dict, values: dict | None = None):
	instance = session.scalar(select(model).filter_by(**lookup))
	if instance is None:
		instance = model(**lookup, **(values or {}))
		session.add(instance)
		session.flush()
	return instance


def seed() -> dict[str, str]:
	passwords = {
		"admin@example.com": seed_password("SEED_ADMIN_PASSWORD"),
		"manager@example.com": seed_password("SEED_MANAGER_PASSWORD"),
		"staff@example.com": seed_password("SEED_STAFF_PASSWORD"),
	}

	with SessionLocal.begin() as session:
		admin = get_or_create(
			session,
			User,
			{"email": "admin@example.com"},
			{
				"full_name": "StockSense Admin",
				"password_hash": password_hasher.hash(passwords["admin@example.com"]),
				"role": UserRole.ADMIN,
			},
		)
		get_or_create(
			session,
			User,
			{"email": "manager@example.com"},
			{
				"full_name": "Inventory Manager",
				"password_hash": password_hasher.hash(passwords["manager@example.com"]),
				"role": UserRole.INVENTORY_MANAGER,
			},
		)
		get_or_create(
			session,
			User,
			{"email": "staff@example.com"},
			{
				"full_name": "Warehouse Staff",
				"password_hash": password_hasher.hash(passwords["staff@example.com"]),
				"role": UserRole.WAREHOUSE_STAFF,
			},
		)

		categories = {
			item: get_or_create(session, Category, {"name": item})
			for item in ("Raw Materials", "Finished Goods", "Components", "Consumables")
		}
		main_warehouse = get_or_create(
			session,
			Warehouse,
			{"code": "MAIN"},
			{"name": "Main Warehouse", "address": "1 StockSense Way"},
		)
		production_warehouse = get_or_create(
			session,
			Warehouse,
			{"code": "PROD"},
			{"name": "Production Warehouse", "address": "2 StockSense Way"},
		)
		locations = {
			"main_rack_a": get_or_create(
				session,
				Location,
				{"warehouse_id": main_warehouse.id, "code": "RACK-A"},
				{"name": "Rack A", "location_type": "STORAGE"},
			),
			"main_rack_b": get_or_create(
				session,
				Location,
				{"warehouse_id": main_warehouse.id, "code": "RACK-B"},
				{"name": "Rack B", "location_type": "STORAGE"},
			),
			"production_floor": get_or_create(
				session,
				Location,
				{"warehouse_id": production_warehouse.id, "code": "FLOOR"},
				{"name": "Production Floor", "location_type": "PRODUCTION"},
			),
		}
		supplier = get_or_create(session, Supplier, {"name": "ABC Metals"}, {"email": "sales@abcmetals.example"})
		customer = get_or_create(session, Customer, {"name": "Demo Customer"}, {"email": "orders@demo.example"})
		del supplier, customer

		products = [
			("Steel Rods", "STEEL-001", categories["Raw Materials"], locations["main_rack_a"], Decimal("100")),
			("Office Chairs", "CHAIR-001", categories["Finished Goods"], locations["main_rack_b"], Decimal("25")),
			("Packaging Boxes", "BOX-001", categories["Consumables"], locations["production_floor"], Decimal("200")),
		]
		for name, sku, category, location, initial_quantity in products:
			product = get_or_create(
				session,
				Product,
				{"sku": sku},
				{
					"name": name,
					"category_id": category.id,
					"unit_of_measure": "units",
					"reorder_level": initial_quantity / 4,
					"reorder_quantity": initial_quantity,
				},
			)
			inventory = session.scalar(
				select(Inventory).where(
					Inventory.product_id == product.id,
					Inventory.location_id == location.id,
				)
			)
			if inventory is None:
				inventory = Inventory(
					product_id=product.id,
					warehouse_id=location.warehouse_id,
					location_id=location.id,
					quantity=initial_quantity,
				)
				session.add(inventory)
				session.flush()
				session.add(
					StockMovement(
						product_id=product.id,
						warehouse_id=location.warehouse_id,
						location_id=location.id,
						movement_type=MovementType.INITIAL_STOCK,
						quantity=initial_quantity,
						quantity_before=Decimal("0"),
						quantity_after=initial_quantity,
						reference_type="SEED",
						reason="Initial demo inventory",
						performed_by=admin.id,
					)
				)

	return passwords


if __name__ == "__main__":
	seeded_passwords = seed()
	print("Seed completed. Generated passwords are shown once:")
	for email, password in seeded_passwords.items():
		print(f"{email}: {password}")