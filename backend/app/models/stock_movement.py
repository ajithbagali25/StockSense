from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base
from ..utils.enums import MovementType


class StockMovement(Base):
	__tablename__ = "stock_movements"
	__table_args__ = (
		Index("ix_stock_movements_product_created", "product_id", "created_at"),
		Index("ix_stock_movements_created_at", "created_at"),
	)

	id: Mapped[int] = mapped_column(primary_key=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
	quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	quantity_before: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	quantity_after: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	reference_type: Mapped[str | None] = mapped_column(String(60))
	reference_id: Mapped[int | None] = mapped_column()
	reason: Mapped[str | None] = mapped_column(Text)
	performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	product = relationship("Product")
	user = relationship("User")
