from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models
from app import health
from app.analytics.router import router as analytics_router
from app.auth.router import router as auth_router
from app.budgets.router import alerts_router
from app.budgets.router import router as budgets_router
from app.core.config import get_settings
from app.core.db import Base, engine
from app.core.logging import setup_logging
from app.expenses.router import router as expenses_router
from app.web.router import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging(get_settings().log_level)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="SpendSmart", lifespan=lifespan)

for r in (
    health.router,
    auth_router,
    expenses_router,
    budgets_router,
    alerts_router,
    analytics_router,
    web_router,
):
    app.include_router(r)
