import enum
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Category(enum.StrEnum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    SUBSCRIPTIONS = "Subscriptions"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    HEALTH = "Health"
    ENTERTAINMENT = "Entertainment"
    OTHER = "Other"


class CategorySource(enum.StrEnum):
    RULES = "rules"
    ML = "ml"
    LLM = "llm"
    MANUAL = "manual"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str]
    merchant: Mapped[str | None]
    category: Mapped[Category] = mapped_column(Enum(Category, native_enum=False))
    category_source: Mapped[CategorySource] = mapped_column(
        Enum(CategorySource, native_enum=False)
    )
    occurred_on: Mapped[date] = mapped_column(default=date.today)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
