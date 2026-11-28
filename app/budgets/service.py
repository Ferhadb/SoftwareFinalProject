"""Budget business logic."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Depends

from app.budgets.schemas import BudgetStatusResponse
from app.models import Alert, Budget, Category
from app.repositories import get_alert_repo, get_budget_repo, get_expense_repo
from app.repositories.alert_repo import AlertRepository
from app.repositories.budget_repo import BudgetRepository
from app.repositories.expense_repo import ExpenseRepository


class BudgetNotFoundError(Exception):
    pass


def has_reached_threshold(
    spent: Decimal,
    monthly_limit: Decimal,
    threshold: int,
) -> bool:
    return spent * 100 >= monthly_limit * threshold


class BudgetService:
    def __init__(
        self,
        budgets: BudgetRepository,
        expenses: ExpenseRepository,
    ) -> None:
        self.budgets = budgets
        self.expenses = expenses

    def upsert(
        self,
        user_id: int,
        category: Category,
        monthly_limit: Decimal,
    ) -> Budget:
        budget = self.budgets.get_for_user(user_id, category)
        try:
            if budget is None:
                budget = self.budgets.add(
                    Budget(
                        user_id=user_id,
                        category=category,
                        monthly_limit=monthly_limit,
                    )
                )
            else:
                budget.monthly_limit = monthly_limit
            self.budgets.commit()
        except Exception:
            self.budgets.rollback()
            raise
        return budget

    def list(self, user_id: int) -> list[Budget]:
        return sorted(
            self.budgets.list_for_user(user_id),
            key=lambda budget: budget.category.value,
        )

    def status(
        self,
        user_id: int,
        month: str | None = None,
    ) -> list[BudgetStatusResponse]:
        month = month or date.today().strftime("%Y-%m")
        return [
            self._status_for_budget(user_id, budget, month)
            for budget in self.list(user_id)
        ]

    def delete(self, user_id: int, category: Category) -> None:
        budget = self.budgets.get_for_user(user_id, category)
        if budget is None:
            raise BudgetNotFoundError
        try:
            self.budgets.delete(budget)
            self.budgets.commit()
        except Exception:
            self.budgets.rollback()
            raise

    def _status_for_budget(
        self,
        user_id: int,
        budget: Budget,
        month: str,
    ) -> BudgetStatusResponse:
        spent = self.expenses.total_for_month(user_id, budget.category, month)
        percent = (spent / budget.monthly_limit * 100).quantize(Decimal("0.01"))
        if has_reached_threshold(spent, budget.monthly_limit, 100):
            level = "exceeded"
        elif has_reached_threshold(spent, budget.monthly_limit, 80):
            level = "warning"
        else:
            level = "ok"
        return BudgetStatusResponse(
            category=budget.category,
            limit=budget.monthly_limit,
            spent=spent,
            percent=percent,
            level=level,
        )


def get_budget_service(
    budgets: Annotated[BudgetRepository, Depends(get_budget_repo)],
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repo)],
) -> BudgetService:
    return BudgetService(budgets, expenses)


class AlertService:
    def __init__(self, alerts: AlertRepository) -> None:
        self.alerts = alerts

    def list(self, user_id: int) -> list[Alert]:
        return self.alerts.list_for_user(user_id)


def get_alert_service(
    alerts: Annotated[AlertRepository, Depends(get_alert_repo)],
) -> AlertService:
    return AlertService(alerts)
