"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from temsafe.api.health import router as health_router
from temsafe.pages import router as pages_router

app = FastAPI(
    title="TEMSAFE API",
    description="Backend API for the TEMSAFE temperature monitoring prototype.",
    version="0.1.0",
)
app.include_router(health_router, prefix="/api")
app.include_router(pages_router)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
