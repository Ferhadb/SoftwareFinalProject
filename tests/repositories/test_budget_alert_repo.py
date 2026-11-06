from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Alert, Budget, Category
from app.repositories import AlertRepository, BudgetRepository


def test_budget_unique_per_user_and_category(db, make_user):
    u = make_user()
    repo = BudgetRepository(db)
    repo.add(Budget(user_id=u.id, category=Category.FOOD, monthly_limit=Decimal(300)))
    assert repo.get_for_user(u.id, Category.FOOD).monthly_limit == Decimal("300.00")
    assert repo.get_for_user(u.id, Category.BILLS) is None
    with pytest.raises(IntegrityError):
        repo.add(Budget(user_id=u.id, category=Category.FOOD, monthly_limit=Decimal(1)))


def test_budget_list_is_scoped(db, make_user):
    a, b = make_user("a@x.com"), make_user("b@x.com")
    repo = BudgetRepository(db)
    repo.add(Budget(user_id=a.id, category=Category.FOOD, monthly_limit=Decimal(1)))
    assert len(repo.list_for_user(a.id)) == 1
    assert repo.list_for_user(b.id) == []


def test_alert_exists_and_unique(db, make_user):
    u = make_user()
    repo = AlertRepository(db)
    assert not repo.exists(u.id, Category.FOOD, 80, "2026-11")
    repo.add(Alert(user_id=u.id, category=Category.FOOD, level=80, month="2026-11"))
    assert repo.exists(u.id, Category.FOOD, 80, "2026-11")
    assert not repo.exists(u.id, Category.FOOD, 100, "2026-11")
    assert not repo.exists(u.id, Category.FOOD, 80, "2026-12")
    with pytest.raises(IntegrityError):
        repo.add(Alert(user_id=u.id, category=Category.FOOD, level=80, month="2026-11"))


def test_alert_list_newest_first_and_scoped(db, make_user):
    a, b = make_user("a@x.com"), make_user("b@x.com")
    repo = AlertRepository(db)
    repo.add(Alert(user_id=a.id, category=Category.FOOD, level=80, month="2026-11"))
    repo.add(Alert(user_id=a.id, category=Category.FOOD, level=100, month="2026-11"))
    assert [x.level for x in repo.list_for_user(a.id)] == [100, 80]
    assert repo.list_for_user(b.id) == []
