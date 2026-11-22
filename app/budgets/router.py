from fastapi import APIRouter

router = APIRouter(prefix="/budgets", tags=["Budgets"])

alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])
