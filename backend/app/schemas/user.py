from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from ..utils.enums import UserRole


class UserCreate(BaseModel):
	full_name: str
	email: EmailStr
	password: str


class UserRead(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	full_name: str
	email: EmailStr
	role: UserRole
	is_active: bool
	created_at: datetime
