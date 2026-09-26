from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	database_url: str
	secret_key: str
	access_token_expire_minutes: int = 60
	otp_expiry_minutes: int = 10

	model_config = SettingsConfigDict(
		env_file=Path(__file__).resolve().parents[2] / ".env",
		env_file_encoding="utf-8",
		extra="ignore",
	)


@lru_cache
def get_settings() -> Settings:
	return Settings()
