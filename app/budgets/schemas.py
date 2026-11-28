"""Request and response schemas for budget endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Category


class BudgetUpsertRequest(BaseModel):
    monthly_limit: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2,
    )


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: Category
    monthly_limit: Decimal


class BudgetStatusResponse(BaseModel):
    category: Category
    limit: Decimal
    spent: Decimal
    percent: Decimal
    level: Literal["ok", "warning", "exceeded"]


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: Category
    level: Literal[80, 100]
    month: str
    created_at: datetime
