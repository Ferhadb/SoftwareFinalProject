from datetime import date
from decimal import Decimal

import pytest

from app.budgets.service import BudgetNotFoundError, BudgetService
from app.models import Category
from app.repositories import BudgetRepository, ExpenseRepository


@pytest.fixture
def service(db):
    return BudgetService(BudgetRepository(db), ExpenseRepository(db))


def test_upsert_creates_and_updates_budget(service, make_user):
    user = make_user()

    created = service.upsert(user.id, Category.FOOD, Decimal("200.00"))
    updated = service.upsert(user.id, Category.FOOD, Decimal("250.00"))

    assert updated.id == created.id
    assert updated.monthly_limit == Decimal("250.00")
    assert service.list(user.id) == [updated]


def test_list_only_returns_users_budgets(service, make_user):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    service.upsert(owner.id, Category.TRANSPORT, Decimal("100.00"))
    service.upsert(owner.id, Category.FOOD, Decimal("200.00"))
    service.upsert(other.id, Category.BILLS, Decimal("300.00"))

    budgets = service.list(owner.id)

    assert [budget.category for budget in budgets] == [
        Category.FOOD,
        Category.TRANSPORT,
    ]


def test_delete_removes_budget(service, make_user):
    user = make_user()
    service.upsert(user.id, Category.FOOD, Decimal("200.00"))

    service.delete(user.id, Category.FOOD)

    assert service.list(user.id) == []


def test_delete_hides_missing_or_another_users_budget(service, make_user):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    service.upsert(owner.id, Category.FOOD, Decimal("200.00"))

    with pytest.raises(BudgetNotFoundError):
        service.delete(other.id, Category.FOOD)


@pytest.mark.parametrize(
    ("spent", "expected_level"),
    [
        ("79.99", "ok"),
        ("80.00", "warning"),
        ("99.99", "warning"),
        ("100.00", "exceeded"),
    ],
)
def test_status_uses_required_level_boundaries(
    service,
    make_user,
    make_expense,
    spent,
    expected_level,
):
    user = make_user()
    service.upsert(user.id, Category.FOOD, Decimal("100.00"))
    make_expense(
        user,
        spent,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 15),
    )

    result = service.status(user.id, "2026-11")

    assert len(result) == 1
    assert result[0].limit == Decimal("100.00")
    assert result[0].spent == Decimal(spent)
    assert result[0].percent == Decimal(spent)
    assert result[0].level == expected_level


def test_status_scopes_spending_by_user_category_and_month(
    service,
    make_user,
    make_expense,
):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    service.upsert(owner.id, Category.FOOD, Decimal("100.00"))
    make_expense(owner, 25, category=Category.FOOD, occurred_on=date(2026, 11, 1))
    make_expense(
        owner,
        40,
        category=Category.TRANSPORT,
        occurred_on=date(2026, 11, 1),
    )
    make_expense(owner, 50, category=Category.FOOD, occurred_on=date(2026, 10, 1))
    make_expense(other, 80, category=Category.FOOD, occurred_on=date(2026, 11, 1))

    result = service.status(owner.id, "2026-11")

    assert result[0].spent == Decimal("25.00")
    assert result[0].percent == Decimal("25.00")
    assert result[0].level == "ok"


def test_status_does_not_use_rounded_percent_for_level(
    service,
    make_user,
    make_expense,
):
    user = make_user()
    service.upsert(user.id, Category.FOOD, Decimal("1000.06"))
    make_expense(
        user,
        800,
        category=Category.FOOD,
        occurred_on=date(2026, 11, 1),
    )

    result = service.status(user.id, "2026-11")

    assert result[0].percent == Decimal("80.00")
    assert result[0].level == "ok"
