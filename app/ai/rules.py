"""Rule-based categorizer: whole-word, case-insensitive keyword matching."""

import re
from collections.abc import Iterable, Mapping

from app.core.monads import Maybe
from app.models import Category

# To support a new merchant, add it to the right list. Keep keywords lowercase.
DEFAULT_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.FOOD: (
        "bravo",
        "araz",
        "bazarstore",
        "wolt",
        "bolt food",
        "uber eats",
        "starbucks",
        "mcdonalds",
        "kfc",
        "cafe",
        "coffee",
        "restaurant",
        "grocery",
        "groceries",
        "supermarket",
        "bakery",
        "pizza",
        "lunch",
        "dinner",
        "breakfast",
    ),
    Category.TRANSPORT: (
        "bolt",
        "uber",
        "taxi",
        "metro",
        "bus",
        "bakikart",
        "azpetrol",
        "fuel",
        "petrol",
        "parking",
        "train",
        "flight",
    ),
    Category.SUBSCRIPTIONS: (
        "netflix",
        "spotify",
        "youtube premium",
        "apple music",
        "icloud",
        "chatgpt",
        "subscription",
    ),
    Category.SHOPPING: (
        "amazon",
        "trendyol",
        "temu",
        "aliexpress",
        "zara",
        "h&m",
        "ikea",
        "mall",
        "clothes",
        "shoes",
    ),
    Category.BILLS: (
        "azercell",
        "bakcell",
        "nar mobile",
        "azerishiq",
        "azeriqaz",
        "azersu",
        "electricity",
        "water bill",
        "gas bill",
        "internet",
        "rent",
        "utilities",
    ),
    Category.HEALTH: (
        "pharmacy",
        "aptek",
        "apteka",
        "doctor",
        "dentist",
        "hospital",
        "clinic",
        "medicine",
        "vitamins",
        "gym",
    ),
    Category.ENTERTAINMENT: (
        "cinema",
        "cinemaplus",
        "park cinema",
        "movie",
        "concert",
        "theatre",
        "theater",
        "museum",
        "bowling",
        "steam",
        "playstation",
    ),
}


class RulesCategorizer:
    name = "rules"

    def __init__(
        self, keywords: Mapping[Category, Iterable[str]] = DEFAULT_KEYWORDS
    ) -> None:
        self._category_of = {
            word.lower(): category
            for category, words in keywords.items()
            for word in words
        }
        # Longest keywords first, so "uber eats" wins over "uber".
        ordered = sorted(self._category_of, key=len, reverse=True)
        alternatives = "|".join(re.escape(word) for word in ordered)
        self._pattern = re.compile(rf"\b(?:{alternatives})\b")

    def categorize(self, description: str) -> Maybe[Category]:
        # Lowercase first, so the matched text is always a key in _category_of.
        match = self._pattern.search(description.lower())
        if match is None:
            return Maybe.nothing()
        return Maybe.of(self._category_of[match.group(0)])
