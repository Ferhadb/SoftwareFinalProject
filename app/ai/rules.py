"""Rule-based categorizer: whole-word, case-insensitive keyword matching."""

import re
from collections.abc import Iterable, Mapping

from app.core.monads import Maybe
from app.models import Category

# To support a new merchant, add it to the right list. Keep keywords lowercase.
# Azerbaijani names are listed with and without special letters (ə, ş),
# because users type both. Dotted and dotless i don't need two spellings.
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
        "azərişıq",
        "azeriqaz",
        "azəriqaz",
        "azersu",
        "azərsu",
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

# Python's lower() turns "I" into "i" and "İ" into "i" plus a combining dot,
# which breaks Azerbaijani text. Folding I, İ and ı to "i" first makes
# "AZƏRİŞIQ", "Azərişıq" and "azərişiq" all look the same.
_FOLD_I = str.maketrans({"I": "i", "İ": "i", "ı": "i"})


def _normalize(text: str) -> str:
    return text.translate(_FOLD_I).lower()


class RulesCategorizer:
    name = "rules"

    def __init__(
        self, keywords: Mapping[Category, Iterable[str]] = DEFAULT_KEYWORDS
    ) -> None:
        self._category_of = {
            _normalize(word): category
            for category, words in keywords.items()
            for word in words
        }
        # Longest keywords first, so "uber eats" wins over "uber".
        ordered = sorted(self._category_of, key=len, reverse=True)
        alternatives = "|".join(re.escape(word) for word in ordered)
        self._pattern = re.compile(rf"\b(?:{alternatives})\b")

    def categorize(self, description: str) -> Maybe[Category]:
        match = self._pattern.search(_normalize(description))
        if match is None:
            return Maybe.nothing()
        return Maybe.of(self._category_of[match.group(0)])
