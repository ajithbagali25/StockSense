from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin
from ..utils.enums import DocumentStatus


class Receipt(TimestampMixin, Base):
	__tablename__ = "receipts"

	id: Mapped[int] = mapped_column(primary_key=True)
	receipt_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
	supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False, index=True)
	received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	validated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
	supplier = relationship("Supplier", back_populates="receipts")
	items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class ReceiptItem(Base):
	__tablename__ = "receipt_items"

	id: Mapped[int] = mapped_column(primary_key=True)
	receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
	quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	receipt = relationship("Receipt", back_populates="items")
	product = relationship("Product")
