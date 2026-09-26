from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user, require_roles
from ...database.session import get_db
from ...models import Category, User
from ...schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from ...services.product_service import create_category, list_categories, update_category
from ...utils.enums import UserRole


router = APIRouter(prefix="/api/categories", tags=["categories"])
write_roles = require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=dict)
def get_categories(
	search: str | None = None,
	page: int = Query(default=1, ge=1),
	limit: int = Query(default=20, ge=1, le=100),
	database: Session = Depends(get_db),
	_: User = Depends(get_current_user),
) -> dict:
	items, total = list_categories(database, search, (page - 1) * limit, limit)
	return {"items": [CategoryRead.model_validate(item) for item in items], "total": total, "page": page, "limit": limit}


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(payload: CategoryCreate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Category:
	try:
		category = create_category(database, payload)
		database.commit()
		database.refresh(category)
		return category
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Category name already exists") from error


@router.put("/{category_id}", response_model=CategoryRead)
def update_category_endpoint(category_id: int, payload: CategoryUpdate, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> Category:
	category = database.scalar(select(Category).where(Category.id == category_id))
	if category is None:
		raise HTTPException(status_code=404, detail="Category not found")
	try:
		category = update_category(database, category, payload)
		database.commit()
		database.refresh(category)
		return category
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Category name already exists") from error


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, database: Session = Depends(get_db), _: User = Depends(write_roles)) -> None:
	category = database.scalar(select(Category).where(Category.id == category_id))
	if category is None:
		raise HTTPException(status_code=404, detail="Category not found")
	database.delete(category)
	try:
		database.commit()
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=409, detail="Category is still used by products") from error
