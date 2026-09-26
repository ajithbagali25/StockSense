from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
	name: str = Field(min_length=1, max_length=180)
	sku: str = Field(min_length=1, max_length=80)
	category_id: int | None = None
	unit_of_measure: str = Field(min_length=1, max_length=30)
	description: str | None = None
	reorder_level: Decimal = Field(default=Decimal("0"), ge=0)
	reorder_quantity: Decimal = Field(default=Decimal("0"), ge=0)


class ProductUpdate(BaseModel):
	name: str | None = Field(default=None, min_length=1, max_length=180)
	sku: str | None = Field(default=None, min_length=1, max_length=80)
	category_id: int | None = None
	unit_of_measure: str | None = Field(default=None, min_length=1, max_length=30)
	description: str | None = None
	reorder_level: Decimal | None = Field(default=None, ge=0)
	reorder_quantity: Decimal | None = Field(default=None, ge=0)
	is_active: bool | None = None


class ProductRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	sku: str
	category_id: int | None
	unit_of_measure: str
	description: str | None
	reorder_level: Decimal
	reorder_quantity: Decimal
	is_active: bool
	created_at: datetime
	updated_at: datetime
