from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..utils.enums import DocumentStatus


class AdjustmentCreate(BaseModel):
	adjustment_number: str = Field(min_length=1, max_length=60)
	product_id: int
	warehouse_id: int
	location_id: int
	counted_quantity: Decimal = Field(ge=0)
	reason: str = Field(min_length=1)


class AdjustmentRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	adjustment_number: str
	product_id: int
	warehouse_id: int
	location_id: int
	system_quantity: Decimal
	counted_quantity: Decimal
	difference: Decimal
	reason: str
	status: DocumentStatus
	created_by: int
	validated_by: int | None
	created_at: datetime
	updated_at: datetime
