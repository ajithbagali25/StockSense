from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from pwdlib import PasswordHash

from .config import get_settings


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
	return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	return password_hasher.verify(password, password_hash)


def create_access_token(subject: str) -> str:
	settings = get_settings()
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
	payload = {"sub": subject, "exp": expires_at, "iat": datetime.now(timezone.utc)}
	return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> str | None:
	try:
		payload = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])
	except JWTError:
		return None
	subject = payload.get("sub")
	return subject if isinstance(subject, str) else None
