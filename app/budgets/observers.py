"""Budget alert observer for newly created expenses."""

import logging
from collections.abc import Callable
from decimal import Decimal
from weakref import WeakSet

from app.budgets.service import has_reached_threshold
from app.core.db import SessionLocal
from app.core.events import EventBus, ExpenseCreated, bus
from app.models import Alert, Category
from app.repositories.alert_repo import AlertRepository
from app.repositories.budget_repo import BudgetRepository
from app.repositories.expense_repo import ExpenseRepository

log = logging.getLogger(__name__)
_registered_buses: WeakSet[EventBus] = WeakSet()


class BudgetAlertObserver:
    def __init__(
        self,
        budgets: BudgetRepository,
        expenses: ExpenseRepository,
        alerts: AlertRepository,
    ) -> None:
        self.budgets = budgets
        self.expenses = expenses
        self.alerts = alerts

    def __call__(self, event: ExpenseCreated) -> None:
        category = Category(event.category)
        budget = self.budgets.get_for_user(event.user_id, category)
        if budget is None:
            return

        spent = self.expenses.total_for_month(
            event.user_id,
            category,
            event.month,
        )
        level = self._reached_level(spent, budget.monthly_limit)
        if level is None or self.alerts.exists(
            event.user_id,
            category,
            level,
            event.month,
        ):
            return

        alert = Alert(
            user_id=event.user_id,
            category=category,
            level=level,
            month=event.month,
        )
        try:
            self.alerts.add(alert)
            self.alerts.commit()
        except Exception:
            self.alerts.rollback()
            raise

        log.warning(
            "budget alert: user_id=%s category=%s level=%s month=%s",
            event.user_id,
            category.value,
            level,
            event.month,
        )

    @staticmethod
    def _reached_level(spent: Decimal, monthly_limit: Decimal) -> int | None:
        if has_reached_threshold(spent, monthly_limit, 100):
            return 100
        if has_reached_threshold(spent, monthly_limit, 80):
            return 80
        return None


def handle_expense_created(
    event: ExpenseCreated,
    session_factory=SessionLocal,
) -> None:
    with session_factory() as db:
        observer = BudgetAlertObserver(
            BudgetRepository(db),
            ExpenseRepository(db),
            AlertRepository(db),
        )
        observer(event)


def register_budget_alert_observer(
    event_bus: EventBus = bus,
    handler: Callable[[ExpenseCreated], None] = handle_expense_created,
) -> None:
    if event_bus in _registered_buses:
        return
    event_bus.subscribe(ExpenseCreated, handler)
    _registered_buses.add(event_bus)
