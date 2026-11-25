"""Checks for data/seed_expenses.csv (TECH_TASK 7.4, issue #15)."""

import csv
from collections import Counter
from pathlib import Path

import pytest

from app.models import Category

SEED = Path(__file__).resolve().parents[1] / "data" / "seed_expenses.csv"


@pytest.fixture(scope="module")
def rows():
    with SEED.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["description", "category"]
        return list(reader)


def test_has_at_least_200_rows(rows):
    assert len(rows) >= 200


def test_every_category_is_valid(rows):
    valid = {c.value for c in Category}
    assert {row["category"] for row in rows} <= valid


def test_every_category_has_at_least_15_rows(rows):
    counts = Counter(row["category"] for row in rows)
    for category in Category:
        assert counts[category.value] >= 15, category.value


def test_descriptions_are_filled_in(rows):
    assert all(row["description"].strip() for row in rows)


def test_no_duplicate_descriptions(rows):
    seen = Counter(row["description"].strip().lower() for row in rows)
    assert [d for d, n in seen.items() if n > 1] == []


def test_english_only_text(rows):
    # The project is English-only: plain ASCII, no local letters.
    assert [r["description"] for r in rows if not r["description"].isascii()] == []
