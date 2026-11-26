from decimal import Decimal

import pytest

from app.core.monads import Maybe
from app.expenses.parser import ParsedExpense, parse_expense_text


@pytest.mark.parametrize(
    ("text", "amount", "description"),
    [
        ("Uber 12.40", "12.40", "Uber"),
        ("Starbucks latte 6.5", "6.5", "Starbucks latte"),
        ("15 Netflix", "15", "Netflix"),
        ("Wolt 12,40", "12.40", "Wolt"),
        ("Bolt $8.25", "8.25", "Bolt"),
        ("Cinema 9.50$", "9.50", "Cinema"),
        ("2 coffees 10", "10", "2 coffees"),
        ("  Uber   12.40  ", "12.40", "Uber"),
    ],
)
def test_parse_expense_text_accepts_supported_formats(text, amount, description):
    result = parse_expense_text(text)

    assert result == Maybe.of(
        ParsedExpense(amount=Decimal(amount), description=description)
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "Uber",
        "Uber 0",
        "Uber -5",
        "Uber 12 0",
        "Uber 12 -5",
        "12.40",
        "Uber NaN",
        "Uber Infinity",
    ],
)
def test_parse_expense_text_rejects_invalid_input(text):
    assert parse_expense_text(text).is_nothing()
