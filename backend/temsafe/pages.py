"""Routes for the web pages."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
templates = Jinja2Templates(directory=FRONTEND_DIR)


@router.get("/index.html", include_in_schema=False)
@router.get("/", include_in_schema=False, name="signin")
def signin(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/pages/dashboard.html", include_in_schema=False, name="dashboard")
def dashboard(request: Request):
    return templates.TemplateResponse(request, "pages/dashboard.html")


@router.get("/pages/history.html", include_in_schema=False, name="history")
def history(request: Request):
    return templates.TemplateResponse(request, "pages/history.html")
