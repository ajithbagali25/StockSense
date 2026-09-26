from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.security import hash_password, verify_password
from ..models import User
from ..schemas.user import UserCreate
from ..utils.enums import UserRole


def register_user(database: Session, payload: UserCreate) -> User:
	user = User(
		full_name=payload.full_name,
		email=payload.email.lower(),
		password_hash=hash_password(payload.password),
		role=UserRole.WAREHOUSE_STAFF,
	)
	database.add(user)
	database.flush()
	return user


def authenticate_user(database: Session, email: str, password: str) -> User | None:
	user = database.scalar(select(User).where(User.email == email.lower()))
	if user is None or not user.is_active or not verify_password(password, user.password_hash):
		return None
	return user
