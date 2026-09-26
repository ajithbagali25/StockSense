from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from .database.connection import engine
from .api.routes.auth import router as auth_router
from .api.routes.categories import router as categories_router
from .api.routes.products import router as products_router
from .api.routes.warehouses import router as warehouses_router
from .api.routes.locations import router as locations_router
from .api.routes.inventory import router as inventory_router
from .api.routes.stock_movements import router as stock_movements_router
from .api.routes.receipts import router as receipts_router
from .api.routes.deliveries import router as deliveries_router


app = FastAPI(
	title="StockSense API",
	description="Modular inventory management system API",
	version="0.1.0",
)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(warehouses_router)
app.include_router(locations_router)
app.include_router(inventory_router)
app.include_router(stock_movements_router)
app.include_router(receipts_router)
app.include_router(deliveries_router)


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
