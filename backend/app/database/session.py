from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from .connection import engine


SessionLocal = sessionmaker(
	bind=engine,
	autocommit=False,
	autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
	database = SessionLocal()
	try:
		yield database
	finally:
		database.close()
