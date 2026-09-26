from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..utils.enums import DocumentStatus


class DeliveryItemCreate(BaseModel):
	product_id: int
	quantity: Decimal = Field(gt=0)


class DeliveryItemRead(DeliveryItemCreate):
	model_config = ConfigDict(from_attributes=True)

	id: int
	picked_quantity: Decimal
	packed_quantity: Decimal


class DeliveryCreate(BaseModel):
	delivery_number: str = Field(min_length=1, max_length=60)
	customer_id: int | None = None
	warehouse_id: int
	location_id: int
	scheduled_at: datetime | None = None
	items: list[DeliveryItemCreate] = Field(min_length=1)


class DeliveryRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	delivery_number: str
	customer_id: int | None
	warehouse_id: int
	location_id: int
	status: DocumentStatus
	scheduled_at: datetime | None
	delivered_at: datetime | None
	created_by: int
	validated_by: int | None
	created_at: datetime
	updated_at: datetime
	items: list[DeliveryItemRead]
