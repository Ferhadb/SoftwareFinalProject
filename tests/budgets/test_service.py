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
