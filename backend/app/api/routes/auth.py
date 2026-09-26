from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user
from ...core.security import create_access_token
from ...database.session import get_db
from ...models import User
from ...schemas.auth import LoginRequest, TokenResponse
from ...schemas.user import UserCreate, UserRead
from ...services.auth_service import authenticate_user, register_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, database: Session = Depends(get_db)) -> User:
	try:
		user = register_user(database, payload)
		database.commit()
		database.refresh(user)
		return user
	except IntegrityError as error:
		database.rollback()
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered") from error


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, database: Session = Depends(get_db)) -> TokenResponse:
	user = authenticate_user(database, payload.email, payload.password)
	if user is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
	user.last_login = datetime.now(timezone.utc)
	database.commit()
	return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
	return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> dict[str, str]:
	return {"message": "Logout acknowledged; discard the bearer token on the client"}
