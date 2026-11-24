"""Categorizer Strategy interface (TECH_TASK 5.6)."""

from typing import Protocol

from app.core.monads import Maybe
from app.models import Category


class CategorizerStrategy(Protocol):
    name: str  # "rules" | "ml" | "llm" | "chain"

    def categorize(self, description: str) -> Maybe[Category]:
        """Return Just(category), or Nothing if this strategy cannot decide."""
        ...
