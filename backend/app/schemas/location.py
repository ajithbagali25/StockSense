from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
	warehouse_id: int
	name: str = Field(min_length=1, max_length=120)
	code: str = Field(min_length=1, max_length=50)
	location_type: str | None = Field(default=None, max_length=80)


class LocationUpdate(BaseModel):
	name: str | None = Field(default=None, min_length=1, max_length=120)
	code: str | None = Field(default=None, min_length=1, max_length=50)
	location_type: str | None = Field(default=None, max_length=80)
	is_active: bool | None = None


class LocationRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	warehouse_id: int
	name: str
	code: str
	location_type: str | None
	is_active: bool
