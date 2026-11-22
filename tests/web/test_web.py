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
    assert "Overview" in response.text
    assert "Quick Add Expense" in response.text


def test_login_page():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    assert "SpendSmart" in response.text
    assert "Welcome Back" in response.text
    assert "Create an Account" in response.text


def test_static_css_served():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "--primary:" in response.text


def test_static_js_served():
    app = get_test_app()
    client = TestClient(app)
    response = client.get("/static/js/api.js")
    assert response.status_code == 200
    assert "SpendSmartApi" in response.text
