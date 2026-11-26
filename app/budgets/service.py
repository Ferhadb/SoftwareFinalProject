"""Budget business logic."""

from decimal import Decimal
from typing import Annotated

from fastapi import Depends

from app.models import Budget, Category
from app.repositories import get_budget_repo, get_expense_repo
from app.repositories.budget_repo import BudgetRepository
from app.repositories.expense_repo import ExpenseRepository


class BudgetNotFoundError(Exception):
    pass


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


def get_budget_service(
    budgets: Annotated[BudgetRepository, Depends(get_budget_repo)],
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repo)],
) -> BudgetService:
    return BudgetService(budgets, expenses)
