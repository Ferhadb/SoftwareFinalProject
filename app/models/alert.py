from datetime import UTC, datetime

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.expense import Category


class Alert(Base):
    __tablename__ = "alerts"
    # one alert per user/category/level/month
    __table_args__ = (UniqueConstraint("user_id", "category", "level", "month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[Category] = mapped_column(Enum(Category, native_enum=False))
    level: Mapped[int]  # 80 or 100
    month: Mapped[str]  # "YYYY-MM"
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
