from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(tags=["Health"])

VERSION = "0.1.0"


@router.get("/health")
def health(response: Response, db: Session = Depends(get_db)):  # noqa: B008
    """Up AND database reachable. UptimeRobot watches this."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = 503
        return {"status": "degraded", "db": "down", "version": VERSION}
    return {"status": "ok", "db": "ok", "version": VERSION}
