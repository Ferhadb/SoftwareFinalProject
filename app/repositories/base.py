from sqlalchemy import select
from sqlalchemy.orm import Session


class Repository[T]:
    """Generic Repository (LC07): the only place that talks to the database."""

    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    def get(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def add(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        self.db.delete(obj)
        self.db.flush()

    def list(self) -> list[T]:
        return list(self.db.scalars(select(self.model)))
