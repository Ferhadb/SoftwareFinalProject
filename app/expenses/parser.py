"""Pure parsing helpers for the expense text input."""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from app.core.monads import Maybe

MONEY_PATTERN = re.compile(r"-?\d{1,10}(?:[.,]\d{1,2})?")


@dataclass(frozen=True)
class ParsedExpense:
    amount: Decimal
    description: str


def _parse_amount(token: str) -> Decimal | None:
    candidate = token.strip().removeprefix("$").removesuffix("$")
    if MONEY_PATTERN.fullmatch(candidate) is None:
        return None

    try:
        amount = Decimal(candidate.replace(",", "."))
    except InvalidOperation:
        return None

    return amount


def parse_expense_text(text: str) -> Maybe[ParsedExpense]:
    """Parse the last positive numeric token as the expense amount."""
    tokens = text.split()
    for index in range(len(tokens) - 1, -1, -1):
        amount = _parse_amount(tokens[index])
        if amount is None:
            continue
        if not amount.is_finite() or amount <= 0:
            return Maybe.nothing()

        description = " ".join([*tokens[:index], *tokens[index + 1 :]]).strip()
        if not description:
            return Maybe.nothing()
        return Maybe.of(ParsedExpense(amount=amount, description=description))

    return Maybe.nothing()
