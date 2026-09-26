from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class Inventory(Base):
	__tablename__ = "inventory"
	__table_args__ = (UniqueConstraint("product_id", "location_id", name="uq_inventory_product_location"),)

	id: Mapped[int] = mapped_column(primary_key=True)
	product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
	location_id: Mapped[int] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
	quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0, nullable=False)
	product = relationship("Product", back_populates="inventory")
	warehouse = relationship("Warehouse")
	location = relationship("Location")
