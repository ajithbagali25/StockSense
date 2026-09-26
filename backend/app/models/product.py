from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin


class Product(TimestampMixin, Base):
	__tablename__ = "products"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
	sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
	category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True)
	unit_of_measure: Mapped[str] = mapped_column(String(30), nullable=False)
	description: Mapped[str | None] = mapped_column(Text)
	reorder_level: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	category = relationship("Category", back_populates="products")
	inventory = relationship("Inventory", back_populates="product")
