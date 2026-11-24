from types import SimpleNamespace

import pytest

from app.ai import factory
from app.ai.factory import ChainCategorizer, build_categorizer, get_categorizer
from app.ai.rules import RulesCategorizer
from app.core.monads import Maybe
from app.models import Category


class FakeStrategy:
    def __init__(self, name, result):
        self.name = name
        self.result = result
        self.calls = 0

    def categorize(self, description):
        self.calls += 1
        return self.result


def test_build_rules():
    assert isinstance(build_categorizer("rules"), RulesCategorizer)


def test_build_chain_starts_with_rules():
    chain = build_categorizer("chain")
    assert isinstance(chain, ChainCategorizer)
    assert isinstance(chain.strategies[0], RulesCategorizer)


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        build_categorizer("magic")


@pytest.mark.parametrize("kind", ["ml", "llm"])
def test_ml_and_llm_not_ready_yet(kind):
    with pytest.raises(NotImplementedError):
        build_categorizer(kind)


def test_chain_returns_first_match_and_stops():
    first = FakeStrategy("rules", Maybe.nothing())
    second = FakeStrategy("ml", Maybe.of(Category.FOOD))
    third = FakeStrategy("llm", Maybe.of(Category.OTHER))
    chain = ChainCategorizer([first, second, third])

    assert chain.categorize("anything") == Maybe.of(Category.FOOD)
    assert third.calls == 0


def test_chain_reports_which_strategy_decided():
    chain = ChainCategorizer(
        [
            FakeStrategy("rules", Maybe.nothing()),
            FakeStrategy("ml", Maybe.of(Category.FOOD)),
        ]
    )
    assert chain.categorize_with_source("x") == Maybe.of((Category.FOOD, "ml"))


def test_chain_returns_nothing_when_all_fail():
    chain = ChainCategorizer([FakeStrategy("rules", Maybe.nothing())])
    assert chain.categorize("x").is_nothing()
    assert chain.categorize_with_source("x").is_nothing()


def test_get_categorizer_uses_settings(monkeypatch):
    monkeypatch.setattr(
        factory, "get_settings", lambda: SimpleNamespace(categorizer="chain")
    )
    assert isinstance(get_categorizer(), ChainCategorizer)


def test_helper_works_with_a_single_strategy():
    rules = build_categorizer("rules")
    assert factory.categorize_with_source(rules, "Bolt ride") == Maybe.of(
        (Category.TRANSPORT, "rules")
    )


def test_helper_works_with_the_chain():
    chain = build_categorizer("chain")
    assert factory.categorize_with_source(chain, "Netflix") == Maybe.of(
        (Category.SUBSCRIPTIONS, "rules")
    )


def test_helper_returns_nothing_when_no_match():
    rules = build_categorizer("rules")
    assert factory.categorize_with_source(rules, "random thing").is_nothing()
