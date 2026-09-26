from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from .database.connection import engine


app = FastAPI(
	title="StockSense API",
	description="Modular inventory management system API",
	version="0.1.0",
)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
	return {"message": "StockSense API is running"}


@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
	return {"status": "healthy"}


@app.get("/api/health/database", tags=["system"])
def database_health_check() -> dict[str, str]:
	try:
		with engine.connect() as connection:
			connection.execute(text("SELECT 1"))
	except Exception as error:
		raise HTTPException(status_code=503, detail="Database unavailable") from error

	return {"status": "healthy", "database": "connected"}
