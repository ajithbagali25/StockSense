from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class Location(Base):
	__tablename__ = "locations"

	id: Mapped[int] = mapped_column(primary_key=True)
	warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
	name: Mapped[str] = mapped_column(String(120), nullable=False)
	code: Mapped[str] = mapped_column(String(50), nullable=False)
	location_type: Mapped[str | None] = mapped_column(String(80))
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	warehouse = relationship("Warehouse", back_populates="locations")
