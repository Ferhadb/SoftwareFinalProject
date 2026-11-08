from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

router = APIRouter(include_in_schema=False)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files directly on sub-path /static
router.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Render the main SpendSmart dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"title": "Dashboard - SpendSmart"},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the user login and registration page."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"title": "Login / Register - SpendSmart"},
    )
