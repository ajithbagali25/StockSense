from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import Category, Location, Product, Warehouse
from ..schemas.category import CategoryCreate, CategoryUpdate
from ..schemas.product import ProductCreate, ProductUpdate


def list_categories(database: Session, search: str | None, skip: int, limit: int) -> tuple[list[Category], int]:
	query = select(Category)
	if search:
		query = query.where(Category.name.ilike(f"%{search}%"))
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	return list(database.scalars(query.order_by(Category.name).offset(skip).limit(limit))), total


def create_category(database: Session, payload: CategoryCreate) -> Category:
	category = Category(**payload.model_dump())
	database.add(category)
	database.flush()
	return category


def update_category(database: Session, category: Category, payload: CategoryUpdate) -> Category:
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(category, field, value)
	database.flush()
	return category


def list_products(
	database: Session,
	search: str | None,
	category_id: int | None,
	include_inactive: bool,
	skip: int,
	limit: int,
) -> tuple[list[Product], int]:
	query = select(Product)
	if search:
		query = query.where(or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%")))
	if category_id is not None:
		query = query.where(Product.category_id == category_id)
	if not include_inactive:
		query = query.where(Product.is_active.is_(True))
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	return list(database.scalars(query.order_by(Product.name).offset(skip).limit(limit))), total


def create_product(database: Session, payload: ProductCreate) -> Product:
	product = Product(**payload.model_dump())
	database.add(product)
	database.flush()
	return product


def update_product(database: Session, product: Product, payload: ProductUpdate) -> Product:
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(product, field, value)
	database.flush()
	return product


def list_warehouses(database: Session, search: str | None, skip: int, limit: int) -> tuple[list[Warehouse], int]:
	query = select(Warehouse)
	if search:
		query = query.where(Warehouse.name.ilike(f"%{search}%") | Warehouse.code.ilike(f"%{search}%"))
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	return list(database.scalars(query.order_by(Warehouse.name).offset(skip).limit(limit))), total


def list_locations(
	database: Session,
	warehouse_id: int | None,
	search: str | None,
	skip: int,
	limit: int,
) -> tuple[list[Location], int]:
	query = select(Location)
	if warehouse_id is not None:
		query = query.where(Location.warehouse_id == warehouse_id)
	if search:
		query = query.where(Location.name.ilike(f"%{search}%") | Location.code.ilike(f"%{search}%"))
	total = database.scalar(select(func.count()).select_from(query.subquery())) or 0
	return list(database.scalars(query.order_by(Location.name).offset(skip).limit(limit))), total
