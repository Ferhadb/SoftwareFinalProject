from datetime import timedelta

import pytest

from app.auth.security import create_access_token, verify_password
from app.core.config import Settings, get_settings
from app.main import app
from app.repositories import UserRepository

TEST_SETTINGS = Settings(
    _env_file=None,
    jwt_secret="integration-test-secret-at-least-32-bytes",
    jwt_expire_minutes=15,
)


@pytest.fixture
def auth_client(client):
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return client


def register(auth_client, email="user@example.com", password="password123"):
    return auth_client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )


def login(auth_client, email="user@example.com", password="password123"):
    return auth_client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )


def test_register_creates_user_with_hashed_password(auth_client, db):
    response = register(auth_client, email="  User@Example.com  ")

    assert response.status_code == 201
    assert response.json() == {"id": 1, "email": "user@example.com"}
    user = UserRepository(db).get_by_email("user@example.com")
    assert user is not None
    assert user.hashed_password != "password123"
    assert verify_password("password123", user.hashed_password)


def test_register_rejects_duplicate_email(auth_client):
    assert register(auth_client).status_code == 201

    response = register(auth_client, email="USER@EXAMPLE.COM")

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_register_rejects_short_password(auth_client):
    response = register(auth_client, password="short")

    assert response.status_code == 422


def test_register_rejects_invalid_email(auth_client):
    response = register(auth_client, email="not-an-email")

    assert response.status_code == 422


def test_login_returns_bearer_token(auth_client):
    register(auth_client)

    response = login(auth_client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_rejects_wrong_password(auth_client):
    register(auth_client)

    response = login(auth_client, password="wrong-password")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_current_user(auth_client):
    register(auth_client)
    token = login(auth_client).json()["access_token"]

    response = auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "email": "user@example.com"}


def test_me_requires_token(auth_client):
    response = auth_client.get("/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_rejects_expired_token(auth_client, make_user):
    user = make_user()
    token = create_access_token(
        user.id,
        settings=TEST_SETTINGS,
        expires_delta=timedelta(seconds=-1),
    )

    response = auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
