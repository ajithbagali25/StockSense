from fastapi import FastAPI


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
