from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.budgets.schemas import BudgetUpsertRequest


def test_budget_limit_accepts_two_decimal_money():
    request = BudgetUpsertRequest(monthly_limit="250.50")

    assert request.monthly_limit == Decimal("250.50")


@pytest.mark.parametrize(
    "monthly_limit",
    [0, -1, "0.001", "99999999999.99"],
)
def test_budget_limit_rejects_invalid_money(monthly_limit):
    with pytest.raises(ValidationError):
        BudgetUpsertRequest(monthly_limit=monthly_limit)
