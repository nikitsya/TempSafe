"""Routes for the web pages."""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Group page routes so main.py can register them on the application together.
router = APIRouter()

# Use the existing frontend folder as the template directory without moving HTML.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
templates = Jinja2Templates(directory=FRONTEND_DIR)


# Both addresses open the sign-in page; HTML routes stay out of the API schema.
@router.get("/index.html", include_in_schema=False)
@router.get("/", include_in_schema=False, name="signin")
def signin(request: Request):
    """Render the sign-in page with the current HTTP request as template context."""
    return templates.TemplateResponse(request, "index.html")


@router.get("/pages/dashboard.html", include_in_schema=False, name="dashboard")
def dashboard(request: Request):
    """Render the dashboard, whose JavaScript currently displays sample readings."""
    return templates.TemplateResponse(request, "pages/dashboard.html")


@router.get("/pages/history.html", include_in_schema=False, name="history")
def history(request: Request):
    """Render the history page, ready for a later connection to the readings API."""
    return templates.TemplateResponse(request, "pages/history.html")
