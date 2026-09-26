from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
	name: str = Field(min_length=1, max_length=120)
	description: str | None = None


class CategoryUpdate(BaseModel):
	name: str | None = Field(default=None, min_length=1, max_length=120)
	description: str | None = None


class CategoryRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	name: str
	description: str | None
	created_at: datetime
	updated_at: datetime
