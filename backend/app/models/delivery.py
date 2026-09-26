from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin
from ..utils.enums import DocumentStatus


class Delivery(TimestampMixin, Base):
	__tablename__ = "deliveries"

	id: Mapped[int] = mapped_column(primary_key=True)
	delivery_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
	customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"))
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False, index=True)
	scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	validated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
	customer = relationship("Customer", back_populates="deliveries")
	items = relationship("DeliveryItem", back_populates="delivery", cascade="all, delete-orphan")


class DeliveryItem(Base):
	__tablename__ = "delivery_items"

	id: Mapped[int] = mapped_column(primary_key=True)
	delivery_id: Mapped[int] = mapped_column(ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
	quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	picked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	packed_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	delivery = relationship("Delivery", back_populates="items")
	product = relationship("Product")
