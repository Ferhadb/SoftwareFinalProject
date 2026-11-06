import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def db():
    """Fresh in-memory SQLite per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db):
    """Factory: make_user("a@x.com") -> persisted User."""
    from app.models import User

    def _make(email="user@example.com", password_hash="x"):
        u = User(email=email.lower(), hashed_password=password_hash)
        db.add(u)
        db.flush()
        return u

    return _make


@pytest.fixture
def make_expense(db):
    """Factory: make_expense(user, 12.5, "Uber", Category.TRANSPORT, date(...))."""
    from datetime import date
    from decimal import Decimal

    from app.models import Category, CategorySource, Expense

    def _make(
        user,
        amount=10,
        description="Thing",
        category=Category.OTHER,
        occurred_on=None,
        merchant=None,
    ):
        e = Expense(
            user_id=user.id,
            amount=Decimal(str(amount)),
            description=description,
            merchant=merchant,
            category=category,
            category_source=CategorySource.RULES,
            occurred_on=occurred_on or date.today(),
        )
        db.add(e)
        db.flush()
        return e

    return _make
