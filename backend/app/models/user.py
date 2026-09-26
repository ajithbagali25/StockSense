from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database.base import Base, TimestampMixin
from ..utils.enums import UserRole


class User(TimestampMixin, Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True)
	full_name: Mapped[str] = mapped_column(String(150), nullable=False)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.WAREHOUSE_STAFF, nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
