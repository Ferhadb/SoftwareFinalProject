import logging
from datetime import date
from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.ai.rules import RulesCategorizer
from app.budgets.observers import (
    BudgetAlertObserver,
    handle_expense_created,
    register_budget_alert_observer,
)
from app.budgets.router import alerts_router
from app.core.events import EventBus, ExpenseCreated
from app.expenses.schemas import ExpenseCreateRequest
from app.expenses.service import ExpenseService
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


def test_event_handler_uses_its_own_session(
    db,
    make_user,
    make_expense,
):
    user = make_user()
    budgets = BudgetRepository(db)
    add_budget(budgets, user)
    make_expense(
        user,
        80,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )
    db.commit()
    session_factory = sessionmaker(bind=db.bind, autoflush=False)

    handle_expense_created(event(user.id), session_factory)
    db.expire_all()

    saved = AlertRepository(db).list_for_user(user.id)
    assert [alert.level for alert in saved] == [80]


def test_registration_is_idempotent():
    event_bus = EventBus()
    seen = []
    register_budget_alert_observer(event_bus, seen.append)
    register_budget_alert_observer(event_bus, seen.append)

    created = event(user_id=1)
    event_bus.publish(created)

    assert seen == [created]


def test_alert_router_registers_observer_at_startup(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.budgets.router.register_budget_alert_observer",
        lambda: calls.append("registered"),
    )
    test_app = FastAPI()
    test_app.include_router(alerts_router)

    with TestClient(test_app):
        pass

    assert calls == ["registered"]


def test_handler_failure_does_not_fail_expense_creation(db, make_user):
    user = make_user()
    event_bus = EventBus()

    def fail(_):
        raise RuntimeError("observer failed")

    event_bus.subscribe(ExpenseCreated, fail)
    service = ExpenseService(ExpenseRepository(db), RulesCategorizer(), event_bus)

    expense = service.create(user.id, ExpenseCreateRequest(text="Uber 12.40"))

    assert expense.id is not None
    assert expense.category == Category.TRANSPORT
