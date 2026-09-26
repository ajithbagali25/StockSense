from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from ..utils.enums import MovementType


class InventoryRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	product_id: int
	warehouse_id: int
	location_id: int
	quantity: Decimal
	reserved_quantity: Decimal
	available_quantity: Decimal


class StockMovementRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	product_id: int
	warehouse_id: int
	location_id: int
	movement_type: MovementType
	quantity: Decimal
	quantity_before: Decimal
	quantity_after: Decimal
	reference_type: str | None
	reference_id: int | None
	reason: str | None
	performed_by: int
	created_at: datetime
