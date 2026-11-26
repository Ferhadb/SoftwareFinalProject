import logging
from datetime import date
from decimal import Decimal

import pytest

from app.ai.rules import RulesCategorizer
from app.core.events import EventBus, ExpenseCreated
from app.expenses.schemas import ExpenseCreateRequest, ExpenseUpdateRequest
from app.expenses.service import (
    ExpenseNotFoundError,
    ExpenseService,
    InvalidExpenseTextError,
)
from app.models import Category, CategorySource
from app.repositories import ExpenseRepository


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def service(db, event_bus):
    return ExpenseService(ExpenseRepository(db), RulesCategorizer(), event_bus)


def test_create_runs_writer_pipeline_and_publishes_event(
    service, make_user, event_bus, caplog
):
    user = make_user()
    events = []
    event_bus.subscribe(ExpenseCreated, events.append)

    with caplog.at_level(logging.INFO, logger="app.expenses.service"):
        expense = service.create(user.id, ExpenseCreateRequest(text="Uber 12.40"))

    assert expense.amount == Decimal("12.40")
    assert expense.description == "Uber"
    assert expense.merchant == "Uber"
    assert expense.category == Category.TRANSPORT
    assert expense.category_source == CategorySource.RULES
    assert events == [
        ExpenseCreated(
            user_id=user.id,
            category=Category.TRANSPORT.value,
            month=date.today().strftime("%Y-%m"),
        )
    ]
    assert "parsed amount=12.40 desc='Uber'" in caplog.text
    assert "categorized as Transport by rules" in caplog.text
    assert f"saved expense id={expense.id}" in caplog.text
    assert "published ExpenseCreated" in caplog.text


def test_create_with_manual_category_sets_manual_source(service, make_user):
    user = make_user()

    expense = service.create(
        user.id,
        ExpenseCreateRequest(
            amount="25.00",
            description="Gift",
            occurred_on=date(2026, 11, 20),
            category=Category.SHOPPING,
        ),
    )

    assert expense.category == Category.SHOPPING
    assert expense.category_source == CategorySource.MANUAL
    assert expense.occurred_on == date(2026, 11, 20)


def test_create_rejects_unparseable_text(service, make_user):
    user = make_user()

    with pytest.raises(InvalidExpenseTextError):
        service.create(user.id, ExpenseCreateRequest(text="Uber"))


def test_list_filters_by_month_and_category(service, make_user, make_expense):
    user = make_user()
    make_expense(user, 5, "Lunch", Category.FOOD, date(2026, 11, 1))
    make_expense(user, 8, "Taxi", Category.TRANSPORT, date(2026, 11, 2))
    make_expense(user, 4, "Dinner", Category.FOOD, date(2026, 10, 1))

    expenses = service.list(user.id, month="2026-11", category=Category.FOOD)

    assert [expense.description for expense in expenses] == ["Lunch"]


def test_get_hides_another_users_expense(service, make_user, make_expense):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    expense = make_expense(owner)

    with pytest.raises(ExpenseNotFoundError):
        service.get(other.id, expense.id)


def test_update_changes_fields_and_marks_category_manual(
    service, make_user, make_expense
):
    user = make_user()
    expense = make_expense(user, description="Old", category=Category.FOOD)

    updated = service.update(
        user.id,
        expense.id,
        ExpenseUpdateRequest(
            amount="15.00",
            description="New",
            category=Category.SHOPPING,
        ),
    )

    assert updated.amount == Decimal("15.00")
    assert updated.description == "New"
    assert updated.merchant == "New"
    assert updated.category == Category.SHOPPING
    assert updated.category_source == CategorySource.MANUAL


def test_delete_removes_expense(service, make_user, make_expense):
    user = make_user()
    expense = make_expense(user)

    service.delete(user.id, expense.id)

    with pytest.raises(ExpenseNotFoundError):
        service.get(user.id, expense.id)
