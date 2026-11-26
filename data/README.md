# Seed expenses

`seed_expenses.csv` holds labelled example expenses for the categorizers
(TECH_TASK §7.4, issue #15). Two columns: `description,category`.

| Category | Rows |
|---|---|
| Food | 121 |
| Shopping | 56 |
| Bills | 40 |
| Entertainment | 40 |
| Health | 40 |
| Other | 40 |
| Subscriptions | 40 |
| Transport | 40 |
| **Total** | **417** |

## What the rows are

Merchant names as they appear on card statements (Baku chains such as Bravo,
Araz and Bazarstore, plus international ones) and short typed descriptions such
as "Doctor appointment" or "Water bill". Only the description is kept: no
amounts, dates, card numbers or names.

## Rules for new rows

- The category is one of the eight `Category` values in `app/models`.
- Plain English text in ASCII; local merchants use Latin spelling
  (`Azerishiq`, not the local letters).
- No duplicates, ignoring case.

`tests/test_seed_data.py` checks all of these, plus the TECH_TASK minimums
(at least 200 rows, at least 15 per category).

## Notes for the ML categorizer (#17)

- Food is the largest class (121 of 417), so report macro-F1 next to accuracy.
- Many merchants appear in several variants (`BRAVO`, `BRAVO 28 MALL`, ...).
  Split train and test by merchant, not by row, or the score mostly measures
  memorized names.
- Public datasets are not mixed into this file; see "Later" in
  `docs/ai-analytics.md`.
