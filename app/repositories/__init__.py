"""Repository providers for FastAPI `Depends`."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repositories.alert_repo import AlertRepository
from app.repositories.budget_repo import BudgetRepository
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.user_repo import UserRepository

DbSession = Annotated[Session, Depends(get_db)]


def get_user_repo(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_expense_repo(db: DbSession) -> ExpenseRepository:
    return ExpenseRepository(db)


def get_budget_repo(db: DbSession) -> BudgetRepository:
    return BudgetRepository(db)


def get_alert_repo(db: DbSession) -> AlertRepository:
    return AlertRepository(db)
