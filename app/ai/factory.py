"""Factory that builds the categorizer chosen by the CATEGORIZER setting."""

from collections.abc import Callable, Iterable

from app.ai.base import CategorizerStrategy
from app.ai.rules import RulesCategorizer
from app.core.config import get_settings
from app.core.monads import Maybe
from app.models import Category


class ChainCategorizer:
    """Tries each strategy in order and returns the first non-Nothing result."""

    name = "chain"

    def __init__(self, strategies: Iterable[CategorizerStrategy]) -> None:
        self.strategies = list(strategies)

    def categorize_with_source(self, description: str) -> Maybe[tuple[Category, str]]:
        """Like categorize(), but also says which strategy decided.

        The expense service needs this to fill category_source.
        """
        for strategy in self.strategies:
            result = strategy.categorize(description)
            if not result.is_nothing():
                return result.map(lambda category, s=strategy: (category, s.name))
        return Maybe.nothing()

    def categorize(self, description: str) -> Maybe[Category]:
        return self.categorize_with_source(description).map(lambda pair: pair[0])


def _not_ready(kind: str) -> Callable[[], CategorizerStrategy]:
    def build() -> CategorizerStrategy:
        raise NotImplementedError(f"the '{kind}' categorizer is not implemented yet")

    return build


# Each kind maps to a function that builds it. ML and LLM are added in #17, #18.
_BUILDERS: dict[str, Callable[[], CategorizerStrategy]] = {
    "rules": RulesCategorizer,
    "chain": lambda: ChainCategorizer([RulesCategorizer()]),
    "ml": _not_ready("ml"),
    "llm": _not_ready("llm"),
}


def build_categorizer(kind: str) -> CategorizerStrategy:
    try:
        builder = _BUILDERS[kind]
    except KeyError:
        raise ValueError(f"unknown categorizer: '{kind}'") from None
    return builder()


def get_categorizer() -> CategorizerStrategy:
    """FastAPI dependency: the categorizer selected by settings."""
    return build_categorizer(get_settings().categorizer)
