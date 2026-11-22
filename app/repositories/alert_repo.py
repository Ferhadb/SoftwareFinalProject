from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Category
from app.repositories.base import Repository


class AlertRepository(Repository[Alert]):
    def __init__(self, db: Session):
        super().__init__(db, Alert)

    def exists(self, user_id: int, category: Category, level: int, month: str) -> bool:
        return (
            self.db.scalar(
                select(Alert.id).where(
                    Alert.user_id == user_id,
                    Alert.category == category,
                    Alert.level == level,
                    Alert.month == month,
                )
            )
            is not None
        )

    def list_for_user(self, user_id: int) -> list[Alert]:
        return list(
            self.db.scalars(
                select(Alert)
                .where(Alert.user_id == user_id)
                .order_by(Alert.created_at.desc(), Alert.id.desc())
            )
        )
