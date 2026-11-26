"""Expense business logic and the Writer-based create pipeline."""

import logging
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Depends

from app.ai.base import CategorizerStrategy
from app.ai.factory import categorize_with_source, get_categorizer
from app.core.events import EventBus, ExpenseCreated, bus
from app.core.monads import Writer
from app.expenses.parser import parse_expense_text
from app.expenses.schemas import ExpenseCreateRequest, ExpenseUpdateRequest
from app.models import Category, CategorySource, Expense
from app.repositories import get_expense_repo
from app.repositories.expense_repo import ExpenseRepository

log = logging.getLogger(__name__)
CENT = Decimal("0.01")


class InvalidExpenseTextError(Exception):
    pass


class ExpenseNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ExpenseDraft:
    amount: Decimal
    description: str
    occurred_on: date
    category: Category | None = None
    category_source: CategorySource | None = None


class ExpenseService:
    def __init__(
        self,
        expenses: ExpenseRepository,
        categorizer: CategorizerStrategy,
        event_bus: EventBus,
    ) -> None:
        self.expenses = expenses
        self.categorizer = categorizer
        self.event_bus = event_bus

    def create(self, user_id: int, request: ExpenseCreateRequest) -> Expense:
        pipeline = (
            self._parse(request)
            .bind(self._categorize)
            .bind(lambda draft: self._save(user_id, draft))
            .bind(self._publish)
        )
        expense, entries = pipeline.run()
        log.info("expense create: %s", " | ".join(entries))
        return expense

    def list(
        self,
        user_id: int,
        month: str | None = None,
        category: Category | None = None,
    ) -> list[Expense]:
        return self.expenses.list_for_user(user_id, month, category)

    def get(self, user_id: int, expense_id: int) -> Expense:
        expense = self.expenses.get_for_user(user_id, expense_id)
        if expense is None:
            raise ExpenseNotFoundError
        return expense

    def update(
        self,
        user_id: int,
        expense_id: int,
        request: ExpenseUpdateRequest,
    ) -> Expense:
        expense = self.get(user_id, expense_id)
        changes = request.model_dump(exclude_unset=True)

        if "amount" in changes:
            expense.amount = changes["amount"]
        if "description" in changes:
            expense.description = changes["description"]
            expense.merchant = changes["description"]
        if "occurred_on" in changes:
            expense.occurred_on = changes["occurred_on"]
        if "category" in changes:
            expense.category = changes["category"]
            expense.category_source = CategorySource.MANUAL

        self._commit_or_rollback()
        return expense

    def delete(self, user_id: int, expense_id: int) -> None:
        expense = self.get(user_id, expense_id)
        try:
            self.expenses.delete(expense)
            self.expenses.commit()
        except Exception:
            self.expenses.rollback()
            raise

    def _parse(self, request: ExpenseCreateRequest) -> Writer[ExpenseDraft]:
        if request.text is not None:
            parsed = parse_expense_text(request.text)
            if parsed.is_nothing():
                raise InvalidExpenseTextError
            value = parsed.get_or_else(None)  # type: ignore[arg-type]
            draft = ExpenseDraft(
                amount=value.amount.quantize(CENT),
                description=value.description,
                occurred_on=date.today(),
            )
        else:
            assert request.amount is not None
            assert request.description is not None
            draft = ExpenseDraft(
                amount=request.amount,
                description=request.description,
                occurred_on=request.occurred_on or date.today(),
                category=request.category,
                category_source=(
                    CategorySource.MANUAL if request.category is not None else None
                ),
            )

        return Writer.unit(draft).tell(
            f"parsed amount={draft.amount:.2f} desc='{draft.description}'"
        )

    def _categorize(self, draft: ExpenseDraft) -> Writer[ExpenseDraft]:
        if draft.category is not None:
            source = draft.category_source or CategorySource.MANUAL
            categorized = replace(draft, category_source=source)
        else:
            result = categorize_with_source(self.categorizer, draft.description)
            if result.is_nothing():
                category = Category.OTHER
                source_name = CategorySource.FALLBACK.value
            else:
                category, source_name = result.get_or_else(
                    (Category.OTHER, CategorySource.RULES.value)
                )
            source = CategorySource(source_name)
            categorized = replace(
                draft,
                category=category,
                category_source=source,
            )

        return Writer.unit(categorized).tell(
            f"categorized as {categorized.category.value} "
            f"by {categorized.category_source.value}"
        )

    def _save(self, user_id: int, draft: ExpenseDraft) -> Writer[Expense]:
        expense = Expense(
            user_id=user_id,
            amount=draft.amount,
            description=draft.description,
            merchant=draft.description,
            category=draft.category,
            category_source=draft.category_source,
            occurred_on=draft.occurred_on,
        )
        try:
            self.expenses.add(expense)
            self.expenses.commit()
        except Exception:
            self.expenses.rollback()
            raise
        return Writer.unit(expense).tell(f"saved expense id={expense.id}")

    def _publish(self, expense: Expense) -> Writer[Expense]:
        self.event_bus.publish(
            ExpenseCreated(
                user_id=expense.user_id,
                category=expense.category.value,
                month=expense.occurred_on.strftime("%Y-%m"),
            )
        )
        return Writer.unit(expense).tell("published ExpenseCreated")

    def _commit_or_rollback(self) -> None:
        try:
            self.expenses.commit()
        except Exception:
            self.expenses.rollback()
            raise


def get_expense_service(
    expenses: Annotated[ExpenseRepository, Depends(get_expense_repo)],
    categorizer: Annotated[CategorizerStrategy, Depends(get_categorizer)],
) -> ExpenseService:
    return ExpenseService(expenses, categorizer, bus)
