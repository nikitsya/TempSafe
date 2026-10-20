"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from temsafe.api.health import router as health_router

app = FastAPI(
    title="TEMSAFE API",
    description="Backend API for the TEMSAFE temperature monitoring prototype.",
    version="0.1.0",
)
app.include_router(health_router, prefix="/api")

# Serve the HTML, CSS and JavaScript frontend from the same address as the API.
# Mounted after the API routes so that /api/... requests still reach the API.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
