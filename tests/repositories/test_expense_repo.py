from datetime import date
from decimal import Decimal

from app.models import Category
from app.repositories import ExpenseRepository
from app.repositories.expense_repo import month_bounds


def test_month_bounds_handles_december():
    assert month_bounds("2026-11") == (date(2026, 11, 1), date(2026, 12, 1))
    assert month_bounds("2026-12") == (date(2026, 12, 1), date(2027, 1, 1))


def test_list_filters_and_orders(db, make_user, make_expense):
    u = make_user()
    make_expense(u, 5, "a", Category.FOOD, date(2026, 11, 1))
    make_expense(u, 6, "b", Category.FOOD, date(2026, 11, 20))
    make_expense(u, 7, "c", Category.BILLS, date(2026, 10, 31))
    repo = ExpenseRepository(db)
    assert [e.description for e in repo.list_for_user(u.id)] == ["b", "a", "c"]
    assert [e.description for e in repo.list_for_user(u.id, month="2026-11")] == [
        "b",
        "a",
    ]
    only = repo.list_for_user(u.id, category=Category.BILLS)
    assert [e.description for e in only] == ["c"]


def test_data_is_scoped_to_user(db, make_user, make_expense):
    a, b = make_user("a@x.com"), make_user("b@x.com")
    e = make_expense(a, 5, "mine", Category.FOOD, date(2026, 11, 2))
    repo = ExpenseRepository(db)
    assert repo.get_for_user(a.id, e.id) is not None
    assert repo.get_for_user(b.id, e.id) is None
    assert repo.list_for_user(b.id) == []
    assert repo.total_for_month(b.id, Category.FOOD, "2026-11") == Decimal("0.00")


def test_total_for_month(db, make_user, make_expense):
    u = make_user()
    make_expense(u, "10.10", "x", Category.FOOD, date(2026, 11, 1))
    make_expense(u, "5.25", "y", Category.FOOD, date(2026, 11, 30))
    make_expense(u, 99, "z", Category.FOOD, date(2026, 12, 1))  # next month
    make_expense(u, 99, "w", Category.BILLS, date(2026, 11, 5))  # other category
    assert ExpenseRepository(db).total_for_month(
        u.id, Category.FOOD, "2026-11"
    ) == Decimal("15.35")


def test_totals_by_category(db, make_user, make_expense):
    u = make_user()
    make_expense(u, 10, "x", Category.FOOD, date(2026, 11, 1))
    make_expense(u, 5, "y", Category.FOOD, date(2026, 11, 2))
    make_expense(u, 3, "z", Category.BILLS, date(2026, 11, 3))
    got = ExpenseRepository(db).totals_by_category(u.id, "2026-11")
    assert got == {Category.FOOD: Decimal("15.00"), Category.BILLS: Decimal("3.00")}


def test_totals_by_month_window_and_order(db, make_user, make_expense):
    u = make_user()
    make_expense(
        u, 1, "old", Category.FOOD, date(2026, 5, 31)
    )  # outside 3-month window
    make_expense(u, 2, "a", Category.FOOD, date(2026, 9, 10))
    make_expense(u, 4, "b", Category.FOOD, date(2026, 11, 1))
    make_expense(u, 8, "c", Category.BILLS, date(2026, 11, 2))
    got = ExpenseRepository(db).totals_by_month(u.id, 3, today=date(2026, 11, 15))
    assert got == [("2026-09", Decimal("2.00")), ("2026-11", Decimal("12.00"))]


def test_totals_by_month_crosses_year(db, make_user, make_expense):
    u = make_user()
    make_expense(u, 3, "dec", Category.FOOD, date(2025, 12, 5))
    got = ExpenseRepository(db).totals_by_month(u.id, 3, today=date(2026, 1, 10))
    assert got == [("2025-12", Decimal("3.00"))]


def test_top_merchants_uses_merchant_or_description(db, make_user, make_expense):
    u = make_user()
    make_expense(u, 5, "Latte", Category.FOOD, date(2026, 11, 1), merchant="Starbucks")
    make_expense(u, 6, "Latte", Category.FOOD, date(2026, 11, 2), merchant="Starbucks")
    make_expense(u, 4, "Uber", Category.TRANSPORT, date(2026, 11, 3))
    make_expense(u, 1, "Gum", Category.FOOD, date(2026, 11, 4))
    got = ExpenseRepository(db).top_merchants(u.id, "2026-11", limit=2)
    assert got == [("Starbucks", Decimal("11.00")), ("Uber", Decimal("4.00"))]
