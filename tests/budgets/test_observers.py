import logging
from datetime import date
from decimal import Decimal

import pytest

from app.budgets.observers import BudgetAlertObserver
from app.core.events import ExpenseCreated
from app.models import Budget, Category
from app.repositories import AlertRepository, BudgetRepository, ExpenseRepository


@pytest.fixture
def repositories(db):
    return (
        BudgetRepository(db),
        ExpenseRepository(db),
        AlertRepository(db),
    )


@pytest.fixture
def observer(repositories):
    return BudgetAlertObserver(*repositories)


def event(user_id, category=Category.FOOD):
    return ExpenseCreated(
        user_id=user_id,
        category=category.value,
        month="2026-11",
    )


def add_budget(repository, user, limit="100.00"):
    repository.add(
        Budget(
            user_id=user.id,
            category=Category.FOOD,
            monthly_limit=Decimal(limit),
        )
    )
    repository.commit()


def test_observer_creates_80_percent_alert_once(
    observer,
    repositories,
    make_user,
    make_expense,
    caplog,
):
    budgets, _, alerts = repositories
    user = make_user()
    add_budget(budgets, user)
    make_expense(
        user,
        80,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )

    with caplog.at_level(logging.WARNING, logger="app.budgets.observers"):
        observer(event(user.id))
        observer(event(user.id))

    saved = alerts.list_for_user(user.id)
    assert [alert.level for alert in saved] == [80]
    assert "category=Food level=80 month=2026-11" in caplog.text


def test_observer_creates_100_percent_alert_once_after_warning(
    observer,
    repositories,
    make_user,
    make_expense,
):
    budgets, _, alerts = repositories
    user = make_user()
    add_budget(budgets, user)
    make_expense(
        user,
        80,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )
    observer(event(user.id))
    make_expense(
        user,
        20,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 2),
    )
    observer(event(user.id))
    make_expense(
        user,
        10,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 3),
    )
    observer(event(user.id))

    saved = alerts.list_for_user(user.id)
    assert sorted(alert.level for alert in saved) == [80, 100]


def test_observer_does_nothing_without_budget(
    observer,
    repositories,
    make_user,
    make_expense,
):
    _, _, alerts = repositories
    user = make_user()
    make_expense(
        user,
        100,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )

    observer(event(user.id))

    assert alerts.list_for_user(user.id) == []


def test_observer_uses_exact_threshold_comparison(
    observer,
    repositories,
    make_user,
    make_expense,
):
    budgets, _, alerts = repositories
    user = make_user()
    add_budget(budgets, user, "1000.06")
    make_expense(
        user,
        800,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )

    observer(event(user.id))

    assert alerts.list_for_user(user.id) == []
