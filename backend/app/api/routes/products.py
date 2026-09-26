from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, require_roles
from ...database.session import get_db
from ...models import Category, Product, User
from ...schemas.product import ProductCreate, ProductRead, ProductUpdate
from ...services.product_service import create_product, list_products, update_product
from ...utils.enums import UserRole


router = APIRouter(prefix="/api/products", tags=["products"])
write_roles = require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=dict)
def get_products(
	search: str | None = None,
	category_id: int | None = None,
	include_inactive: bool = False,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	items, total = list_products(database, search, category_id, include_inactive, (page - 1) * limit, limit)
	return {"items": [ProductRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(payload: ProductCreate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Product:
	if payload.category_id is not None and database.scalar(select(Category).where(Category.id == payload.category_id)) is None:
		raise HTTPException(status_code=404, detail="Category not found")
	try:
		product = create_product(database, payload)
		database.commit()
		database.refresh(product)
		return product
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="SKU already exists") from error


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Product:
	product = database.scalar(select(Product).where(Product.id == product_id))
	if product is None:
		raise HTTPException(status_code=404, detail="Product not found")
	return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product_endpoint(product_id: int, payload: ProductUpdate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Product:
	product = database.scalar(select(Product).where(Product.id == product_id))
	if product is None:
		raise HTTPException(status_code=404, detail="Product not found")
	try:
		product = update_product(database, product, payload)
		database.commit()
		database.refresh(product)
		return product
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="SKU already exists") from error


@router.delete("/{product_id}", response_model=ProductRead)
def disable_product(product_id: int, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Product:
	product = database.scalar(select(Product).where(Product.id == product_id))
	if product is None:
		raise HTTPException(status_code=404, detail="Product not found")
	product.is_active = False
	database.commit()
	database.refresh(product)
	return product
