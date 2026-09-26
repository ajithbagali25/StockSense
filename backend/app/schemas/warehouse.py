from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehouseCreate(BaseModel):
	name: str = Field(min_length=1, max_length=120)
	code: str = Field(min_length=1, max_length=50)
	address: str | None = None


class WarehouseUpdate(BaseModel):
	name: str | None = Field(default=None, min_length=1, max_length=120)
	code: str | None = Field(default=None, min_length=1, max_length=50)
	address: str | None = None
	is_active: bool | None = None


class WarehouseRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	code: str
	address: str | None
	is_active: bool
	created_at: datetime
	updated_at: datetime
