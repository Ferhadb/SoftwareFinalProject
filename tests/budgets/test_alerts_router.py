from datetime import UTC, datetime

import pytest

from app.auth.security import create_access_token
from app.core.config import Settings, get_settings
from app.main import app
from app.models import Alert, Category

TEST_SETTINGS = Settings(
    _env_file=None,
    jwt_secret="alert-test-secret-at-least-32-bytes",
)


@pytest.fixture
def alert_client(client):
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return client


def auth_headers(user):
    token = create_access_token(user.id, settings=TEST_SETTINGS)
    return {"Authorization": f"Bearer {token}"}


def add_alert(db, user, category, level, month, created_at):
    alert = Alert(
        user_id=user.id,
        category=category,
        level=level,
        month=month,
        created_at=created_at,
    )
    db.add(alert)
    db.flush()
    return alert


def test_alerts_require_authentication(alert_client):
    response = alert_client.get("/alerts")

    assert response.status_code == 401


def test_list_alerts_is_scoped_and_newest_first(alert_client, db, make_user):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    add_alert(
        db,
        owner,
        Category.FOOD,
        80,
        "2026-10",
        datetime(2026, 10, 1, tzinfo=UTC),
    )
    add_alert(
        db,
        owner,
        Category.FOOD,
        100,
        "2026-11",
        datetime(2026, 11, 1, tzinfo=UTC),
    )
    add_alert(
        db,
        other,
        Category.BILLS,
        80,
        "2026-12",
        datetime(2026, 12, 1, tzinfo=UTC),
    )

    response = alert_client.get("/alerts", headers=auth_headers(owner))

    assert response.status_code == 200
    assert [item["level"] for item in response.json()] == [100, 80]
    assert {item["category"] for item in response.json()} == {"Food"}
