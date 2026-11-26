from datetime import date

import pytest

from app.auth.security import create_access_token
from app.core.config import Settings, get_settings
from app.main import app
from app.models import Category

TEST_SETTINGS = Settings(
    _env_file=None,
    jwt_secret="budget-test-secret-at-least-32-bytes",
)


@pytest.fixture
def budget_client(client):
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return client


def auth_headers(user):
    token = create_access_token(user.id, settings=TEST_SETTINGS)
    return {"Authorization": f"Bearer {token}"}


def test_budgets_require_authentication(budget_client):
    assert budget_client.get("/budgets").status_code == 401
    assert budget_client.get("/budgets/status").status_code == 401
    assert (
        budget_client.put(
            "/budgets/Food",
            json={"monthly_limit": 100},
        ).status_code
        == 401
    )
    assert budget_client.delete("/budgets/Food").status_code == 401


def test_put_creates_and_updates_budget(budget_client, make_user):
    user = make_user()
    headers = auth_headers(user)

    created = budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": "200.00"},
        headers=headers,
    )
    updated = budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": "250.00"},
        headers=headers,
    )

    assert created.status_code == 200
    assert updated.status_code == 200
    assert updated.json() == {
        "category": "Food",
        "monthly_limit": "250.00",
    }
    assert budget_client.get("/budgets", headers=headers).json() == [updated.json()]


@pytest.mark.parametrize("monthly_limit", [0, -1, "0.001", "99999999999.99"])
def test_put_rejects_invalid_limit(budget_client, make_user, monthly_limit):
    user = make_user()

    response = budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": monthly_limit},
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_list_only_returns_users_budgets(budget_client, make_user):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": 200},
        headers=auth_headers(owner),
    )
    budget_client.put(
        "/budgets/Bills",
        json={"monthly_limit": 300},
        headers=auth_headers(other),
    )

    response = budget_client.get("/budgets", headers=auth_headers(owner))

    assert response.status_code == 200
    assert [budget["category"] for budget in response.json()] == ["Food"]


def test_status_returns_monthly_spending(budget_client, make_user, make_expense):
    user = make_user()
    headers = auth_headers(user)
    budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": 100},
        headers=headers,
    )
    make_expense(
        user,
        "80.00",
        category=Category.FOOD,
        occurred_on=date(2026, 11, 15),
    )

    response = budget_client.get(
        "/budgets/status?month=2026-11",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "category": "Food",
            "limit": "100.00",
            "spent": "80.00",
            "percent": "80.00",
            "level": "warning",
        }
    ]


def test_status_rejects_invalid_month(budget_client, make_user):
    user = make_user()

    response = budget_client.get(
        "/budgets/status?month=2026-13",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_delete_budget_and_hide_another_users_budget(budget_client, make_user):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    owner_headers = auth_headers(owner)
    budget_client.put(
        "/budgets/Food",
        json={"monthly_limit": 200},
        headers=owner_headers,
    )

    hidden = budget_client.delete("/budgets/Food", headers=auth_headers(other))
    deleted = budget_client.delete("/budgets/Food", headers=owner_headers)
    missing = budget_client.delete("/budgets/Food", headers=owner_headers)

    assert hidden.status_code == 404
    assert deleted.status_code == 204
    assert missing.status_code == 404
