from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin


class Warehouse(TimestampMixin, Base):
	__tablename__ = "warehouses"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(120), nullable=False)
	code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
	address: Mapped[str | None] = mapped_column(Text)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	locations = relationship("Location", back_populates="warehouse")
