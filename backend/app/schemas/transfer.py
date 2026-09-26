from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..utils.enums import DocumentStatus


class TransferItemCreate(BaseModel):
	product_id: int
	quantity: Decimal = Field(gt=0)


class TransferItemRead(TransferItemCreate):
	model_config = ConfigDict(from_attributes=True)

	id: int


class TransferCreate(BaseModel):
	transfer_number: str = Field(min_length=1, max_length=60)
	source_warehouse_id: int
	source_location_id: int
	destination_warehouse_id: int
	destination_location_id: int
	scheduled_at: datetime | None = None
	items: list[TransferItemCreate] = Field(min_length=1)


class TransferRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	transfer_number: str
	source_warehouse_id: int
	source_location_id: int
	destination_warehouse_id: int
	destination_location_id: int
	status: DocumentStatus
	scheduled_at: datetime | None
	completed_at: datetime | None
	created_by: int
	created_at: datetime
	updated_at: datetime
	items: list[TransferItemRead]
