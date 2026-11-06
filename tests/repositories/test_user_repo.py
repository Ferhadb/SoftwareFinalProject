import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.repositories import UserRepository


def test_add_get_and_get_by_email(db):
    repo = UserRepository(db)
    u = repo.add(User(email="a@x.com", hashed_password="h"))
    assert repo.get(u.id).email == "a@x.com"
    assert repo.get_by_email("A@X.com").id == u.id
    assert repo.get_by_email("nobody@x.com") is None


def test_email_is_unique(db):
    repo = UserRepository(db)
    repo.add(User(email="a@x.com", hashed_password="h"))
    with pytest.raises(IntegrityError):
        repo.add(User(email="a@x.com", hashed_password="h2"))


def test_list_and_delete(db):
    repo = UserRepository(db)
    u = repo.add(User(email="a@x.com", hashed_password="h"))
    assert len(repo.list()) == 1
    repo.delete(u)
    assert repo.list() == []
