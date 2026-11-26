"""Request and response schemas for expense endpoints."""

from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import Category, CategorySource


class ExpenseCreateRequest(BaseModel):
    text: str | None = None
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    description: str | None = None
    occurred_on: date | None = None
    category: Category | None = None

    @field_validator("text", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value must not be blank")
        return stripped

    @model_validator(mode="after")
    def validate_input_mode(self) -> Self:
        if self.text is not None:
            structured = (
                self.amount,
                self.description,
                self.occurred_on,
                self.category,
            )
            if any(value is not None for value in structured):
                raise ValueError("Use either text or structured expense fields")
            return self

        if self.amount is None or self.description is None:
            raise ValueError("Structured expenses require amount and description")
        return self


class ExpenseUpdateRequest(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    description: str | None = None
    occurred_on: date | None = None
    category: Category | None = None

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Description must not be blank")
        return stripped

    @model_validator(mode="after")
    def require_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Expense fields cannot be null")
        return self


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    merchant: str | None
    category: Category
    category_source: CategorySource
    occurred_on: date
    created_at: datetime
