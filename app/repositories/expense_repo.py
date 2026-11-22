from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Expense
from app.repositories.base import Repository

TWO = Decimal("0.01")


def month_bounds(month: str) -> tuple[date, date]:
    """'2026-11' -> (2026-11-01, 2026-12-01); end is exclusive."""
    y, m = (int(p) for p in month.split("-"))
    return date(y, m, 1), date(y + (m == 12), m % 12 + 1, 1)


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(TWO)


class ExpenseRepository(Repository[Expense]):
    def __init__(self, db: Session):
        super().__init__(db, Expense)

    def list_for_user(
        self,
        user_id: int,
        month: str | None = None,
        category: Category | None = None,
    ) -> list[Expense]:
        q = select(Expense).where(Expense.user_id == user_id)
        if month:
            start, end = month_bounds(month)
            q = q.where(Expense.occurred_on >= start, Expense.occurred_on < end)
        if category:
            q = q.where(Expense.category == category)
        q = q.order_by(Expense.occurred_on.desc(), Expense.id.desc())
        return list(self.db.scalars(q))

    def get_for_user(self, user_id: int, expense_id: int) -> Expense | None:
        return self.db.scalar(
            select(Expense).where(Expense.user_id == user_id, Expense.id == expense_id)
        )

    def total_for_month(self, user_id: int, category: Category, month: str) -> Decimal:
        start, end = month_bounds(month)
        total = self.db.scalar(
            select(func.sum(Expense.amount)).where(
                Expense.user_id == user_id,
                Expense.category == category,
                Expense.occurred_on >= start,
                Expense.occurred_on < end,
            )
        )
        return _money(total)

    def totals_by_category(self, user_id: int, month: str) -> dict[Category, Decimal]:
        start, end = month_bounds(month)
        rows = self.db.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(
                Expense.user_id == user_id,
                Expense.occurred_on >= start,
                Expense.occurred_on < end,
            )
            .group_by(Expense.category)
        )
        return {cat: _money(total) for cat, total in rows}

    def totals_by_month(
        self, user_id: int, months: int, today: date | None = None
    ) -> list[tuple[str, Decimal]]:
        """Totals for the last `months` months, oldest first. Empty months are omitted."""
        today = today or date.today()
        idx = today.year * 12 + today.month - 1 - (months - 1)
        start = date(idx // 12, idx % 12 + 1, 1)
        year = func.extract("year", Expense.occurred_on)
        month = func.extract("month", Expense.occurred_on)
        rows = self.db.execute(
            select(year, month, func.sum(Expense.amount))
            .where(Expense.user_id == user_id, Expense.occurred_on >= start)
            .group_by(year, month)
            .order_by(year, month)
        )
        return [(f"{int(y):04d}-{int(m):02d}", _money(t)) for y, m, t in rows]

    def top_merchants(
        self, user_id: int, month: str, limit: int = 5
    ) -> list[tuple[str, Decimal]]:
        start, end = month_bounds(month)
        name = func.coalesce(Expense.merchant, Expense.description)
        total = func.sum(Expense.amount)
        rows = self.db.execute(
            select(name, total)
            .where(
                Expense.user_id == user_id,
                Expense.occurred_on >= start,
                Expense.occurred_on < end,
            )
            .group_by(name)
            .order_by(total.desc(), name)
            .limit(limit)
        )
        return [(n, _money(t)) for n, t in rows]
