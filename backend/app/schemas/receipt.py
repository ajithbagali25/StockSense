from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ..utils.enums import DocumentStatus


class ReceiptItemCreate(BaseModel):
	product_id: int
	quantity: Decimal = Field(gt=0)


class ReceiptItemRead(ReceiptItemCreate):
	model_config = ConfigDict(from_attributes=True)

	id: int


class ReceiptCreate(BaseModel):
	receipt_number: str = Field(min_length=1, max_length=60)
	supplier_id: int | None = None
	warehouse_id: int
	location_id: int
	items: list[ReceiptItemCreate] = Field(min_length=1)


class ReceiptUpdate(BaseModel):
	supplier_id: int | None = None
	warehouse_id: int | None = None
	location_id: int | None = None
	status: DocumentStatus | None = None
	items: list[ReceiptItemCreate] | None = Field(default=None, min_length=1)


class ReceiptRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	receipt_number: str
	supplier_id: int | None
	warehouse_id: int
	location_id: int
	status: DocumentStatus
	received_at: datetime | None
	created_by: int
	validated_by: int | None
	created_at: datetime
	updated_at: datetime
	items: list[ReceiptItemRead]
