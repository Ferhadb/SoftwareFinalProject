import pytest

from app.ai.rules import RulesCategorizer
from app.core.monads import Maybe
from app.models import Category


@pytest.fixture
def rules():
    return RulesCategorizer()


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("Bravo supermarket", Category.FOOD),
        ("Wolt order", Category.FOOD),
        ("Bolt ride home", Category.TRANSPORT),
        ("BakıKart top-up", Category.TRANSPORT),
        ("Netflix monthly", Category.SUBSCRIPTIONS),
        ("Spotify", Category.SUBSCRIPTIONS),
        ("Trendyol order", Category.SHOPPING),
        ("H&M jacket", Category.SHOPPING),
        ("Azercell balance", Category.BILLS),
        ("Azərişıq electricity", Category.BILLS),
        ("Zeytun aptek", Category.HEALTH),
        ("Dentist visit", Category.HEALTH),
        ("CinemaPlus tickets", Category.ENTERTAINMENT),
        ("Steam game", Category.ENTERTAINMENT),
    ],
)
def test_known_descriptions(rules, description, expected):
    assert rules.categorize(description) == Maybe.of(expected)


def test_case_insensitive(rules):
    assert rules.categorize("NETFLIX") == Maybe.of(Category.SUBSCRIPTIONS)


def test_whole_word_only(rules):
    # "bus" is a keyword, but it must not match inside "business".
    assert rules.categorize("business lunch").get_or_else(None) == Category.FOOD
    assert rules.categorize("busy day").is_nothing()


@pytest.mark.parametrize("text", ["AZƏRİŞIQ", "Azərişıq", "azərişiq"])
def test_azerbaijani_capitals_and_dotless_i(rules, text):
    assert rules.categorize(text) == Maybe.of(Category.BILLS)


def test_nar_juice_is_not_a_phone_bill(rules):
    assert rules.categorize("nar şirəsi").is_nothing()
    assert rules.categorize("Nar Mobile balance") == Maybe.of(Category.BILLS)


def test_longer_keyword_wins(rules):
    assert rules.categorize("Uber Eats burger") == Maybe.of(Category.FOOD)
    assert rules.categorize("Uber to airport") == Maybe.of(Category.TRANSPORT)


def test_unknown_returns_nothing(rules):
    assert rules.categorize("random thing 123").is_nothing()
    assert rules.categorize("").is_nothing()


def test_custom_keywords_are_easy_to_add():
    rules = RulesCategorizer({Category.HEALTH: ["yoga"]})
    assert rules.categorize("Yoga class") == Maybe.of(Category.HEALTH)
    assert rules.categorize("Netflix").is_nothing()
