from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Budget, Category
from app.repositories.base import Repository


class BudgetRepository(Repository[Budget]):
    def __init__(self, db: Session):
        super().__init__(db, Budget)

    def get_for_user(self, user_id: int, category: Category) -> Budget | None:
        return self.db.scalar(
            select(Budget).where(Budget.user_id == user_id, Budget.category == category)
        )

    def list_for_user(self, user_id: int) -> list[Budget]:
        return list(self.db.scalars(select(Budget).where(Budget.user_id == user_id)))
