from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.expenses.schemas import ExpenseCreateRequest, ExpenseUpdateRequest
from app.models import Category


def test_create_request_accepts_text_input():
    request = ExpenseCreateRequest(text="  Uber 12.40  ")

    assert request.text == "Uber 12.40"


def test_create_request_accepts_structured_input():
    request = ExpenseCreateRequest(
        amount="12.40",
        description="  Uber  ",
        occurred_on=date(2026, 11, 20),
        category=Category.TRANSPORT,
    )

    assert request.amount == Decimal("12.40")
    assert request.description == "Uber"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": "   "},
        {"amount": "12.40"},
        {"description": "Uber"},
        {"text": "Uber 12.40", "amount": "12.40", "description": "Uber"},
        {"amount": "0", "description": "Uber"},
        {"amount": "12.345", "description": "Uber"},
    ],
)
def test_create_request_rejects_invalid_input(body):
    with pytest.raises(ValidationError):
        ExpenseCreateRequest.model_validate(body)


def test_update_request_accepts_partial_update():
    request = ExpenseUpdateRequest(category=Category.FOOD)

    assert request.model_dump(exclude_unset=True) == {"category": Category.FOOD}


@pytest.mark.parametrize("body", [{}, {"description": "  "}, {"amount": None}])
def test_update_request_rejects_empty_changes(body):
    with pytest.raises(ValidationError):
        ExpenseUpdateRequest.model_validate(body)
