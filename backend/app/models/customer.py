from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base, TimestampMixin


class Customer(TimestampMixin, Base):
	__tablename__ = "customers"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(160), nullable=False)
	email: Mapped[str | None] = mapped_column(String(255))
	phone: Mapped[str | None] = mapped_column(String(40))
	address: Mapped[str | None] = mapped_column(Text)
	deliveries = relationship("Delivery", back_populates="customer")
