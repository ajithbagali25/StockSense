from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin
from ..utils.enums import DocumentStatus


class Adjustment(TimestampMixin, Base):
	__tablename__ = "adjustments"

	id: Mapped[int] = mapped_column(primary_key=True)
	adjustment_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	system_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	counted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	difference: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	reason: Mapped[str] = mapped_column(Text, nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False, index=True)
	created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	validated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
	product = relationship("Product")
