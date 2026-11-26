from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.web.router import router as web_router


def get_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(web_router)
    return app


def test_dashboard_page():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "SpendSmart" in response.text
    assert "Add expense" in response.text
    assert 'id="trend-chart"' in response.text


def test_login_page():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "SpendSmart" in response.text
    assert "Sign in" in response.text
    assert "Create an account" in response.text


def test_static_css_served():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "--accent:" in response.text
    assert '[data-theme="dark"]' in response.text


def test_static_js_served():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/static/js/api.js")
    assert response.status_code == 200
    assert "SpendSmartApi" in response.text
