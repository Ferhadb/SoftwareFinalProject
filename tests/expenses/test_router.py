from datetime import date

import pytest

from app.auth.security import create_access_token
from app.core.config import Settings, get_settings
from app.main import app
from app.models import Category

TEST_SETTINGS = Settings(
    _env_file=None,
    jwt_secret="expense-test-secret-at-least-32-bytes",
)


@pytest.fixture
def expense_client(client):
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return client


def auth_headers(user):
    token = create_access_token(user.id, settings=TEST_SETTINGS)
    return {"Authorization": f"Bearer {token}"}


def test_expenses_require_authentication(expense_client):
    response = expense_client.get("/expenses")

    assert response.status_code == 401


def test_create_expense_from_text(expense_client, make_user):
    user = make_user()

    response = expense_client.post(
        "/expenses",
        json={"text": "Uber 12.40"},
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "12.40"
    assert body["description"] == "Uber"
    assert body["merchant"] == "Uber"
    assert body["category"] == "Transport"
    assert body["category_source"] == "rules"


def test_create_structured_expense_with_manual_category(expense_client, make_user):
    user = make_user()

    response = expense_client.post(
        "/expenses",
        json={
            "amount": 25,
            "description": "Gift",
            "occurred_on": "2026-11-20",
            "category": "Shopping",
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "Shopping"
    assert body["category_source"] == "manual"
    assert body["occurred_on"] == "2026-11-20"


@pytest.mark.parametrize(
    "body",
    [
        {"text": "Uber"},
        {"amount": 0, "description": "Uber"},
    ],
)
def test_create_rejects_invalid_input(expense_client, make_user, body):
    user = make_user()

    response = expense_client.post(
        "/expenses",
        json=body,
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_list_filters_by_month_and_category(expense_client, make_user, make_expense):
    user = make_user()
    make_expense(user, 5, "Lunch", Category.FOOD, date(2026, 11, 1))
    make_expense(user, 8, "Taxi", Category.TRANSPORT, date(2026, 11, 2))
    make_expense(user, 4, "Dinner", Category.FOOD, date(2026, 10, 1))

    response = expense_client.get(
        "/expenses?month=2026-11&category=Food",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert [item["description"] for item in response.json()] == ["Lunch"]


def test_list_rejects_invalid_month(expense_client, make_user):
    user = make_user()

    response = expense_client.get(
        "/expenses?month=2026-13",
        headers=auth_headers(user),
    )

    assert response.status_code == 422


def test_get_expense(expense_client, make_user, make_expense):
    user = make_user()
    expense = make_expense(user, description="Lunch")

    response = expense_client.get(
        f"/expenses/{expense.id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Lunch"


def test_update_expense_marks_category_manual(expense_client, make_user, make_expense):
    user = make_user()
    expense = make_expense(user, category=Category.FOOD)

    response = expense_client.patch(
        f"/expenses/{expense.id}",
        json={"category": "Shopping"},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["category"] == "Shopping"
    assert response.json()["category_source"] == "manual"


def test_delete_expense(expense_client, make_user, make_expense):
    user = make_user()
    expense = make_expense(user)
    headers = auth_headers(user)

    response = expense_client.delete(f"/expenses/{expense.id}", headers=headers)

    assert response.status_code == 204
    assert (
        expense_client.get(f"/expenses/{expense.id}", headers=headers).status_code
        == 404
    )


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_user_cannot_access_another_users_expense(
    expense_client,
    make_user,
    make_expense,
    method,
):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    expense = make_expense(owner)
    request = getattr(expense_client, method)
    kwargs = {"json": {"description": "Changed"}} if method == "patch" else {}

    response = request(
        f"/expenses/{expense.id}",
        headers=auth_headers(other),
        **kwargs,
    )

    assert response.status_code == 404
