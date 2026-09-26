from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin
from ..utils.enums import DocumentStatus


class Transfer(TimestampMixin, Base):
	__tablename__ = "transfers"

	id: Mapped[int] = mapped_column(primary_key=True)
	transfer_number: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
	source_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	source_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	destination_warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
	destination_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
	status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.DRAFT, nullable=False, index=True)
	scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
	created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	items = relationship("TransferItem", back_populates="transfer", cascade="all, delete-orphan")


class TransferItem(Base):
	__tablename__ = "transfer_items"

	id: Mapped[int] = mapped_column(primary_key=True)
	transfer_id: Mapped[int] = mapped_column(ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
	quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
	transfer = relationship("Transfer", back_populates="items")
	product = relationship("Product")
