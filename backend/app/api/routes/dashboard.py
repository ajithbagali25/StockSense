from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.dependencies import get_current_user
from ...database.session import get_db
from ...models import User
from ...services.dashboard_service import dashboard_summary, low_stock, out_of_stock, pending_count
from ...models import Adjustment, Delivery, Receipt, Transfer


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def filters(warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None) -> dict[str, int | None]:
	return {"warehouse_id": warehouse_id, "location_id": location_id, "category_id": category_id}


@router.get("/summary")
def summary(warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
	return dashboard_summary(database, warehouse_id, location_id, category_id)


@router.get("/low-stock")
def low_stock_items(warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
	return low_stock(database, warehouse_id, location_id, category_id)


@router.get("/out-of-stock")
def out_of_stock_items(warehouse_id: int | None = None, location_id: int | None = None, category_id: int | None = None, database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
	return out_of_stock(database, warehouse_id, location_id, category_id)


@router.get("/pending-receipts")
def pending_receipts(database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, int]:
	return {"count": pending_count(database, Receipt)}


@router.get("/pending-deliveries")
def pending_deliveries(database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, int]:
	return {"count": pending_count(database, Delivery)}


@router.get("/pending-transfers")
def pending_transfers(database: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict[str, int]:
	return {"count": pending_count(database, Transfer)}
