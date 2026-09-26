from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..models import User
from ..utils.enums import UserRole
from .security import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
	database: Session = Depends(get_db),
) -> User:
	unauthorized = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Invalid or missing authentication token",
		headers={"WWW-Authenticate": "Bearer"},
	)
	if credentials is None:
		raise unauthorized
	subject = decode_access_token(credentials.credentials)
	if subject is None:
		raise unauthorized
	user = database.scalar(select(User).where(User.id == int(subject), User.is_active.is_(True)))
	if user is None:
		raise unauthorized
	return user


def require_roles(*roles: UserRole) -> Callable:
	def role_dependency(current_user: User = Depends(get_current_user)) -> User:
		if current_user.role not in roles:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
		return current_user

	return role_dependency
