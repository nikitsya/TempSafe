"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tempsafe.api.auth import router as auth_router
from tempsafe.api.boxes import router as boxes_router
from tempsafe.api.configuration import router as configuration_router
from tempsafe.api.health import router as health_router
from tempsafe.api.readings import router as readings_router
from tempsafe.mqtt import lifespan
from tempsafe.pages import router as pages_router

# Create the application and set the information shown in the API documentation.
app = FastAPI(
    lifespan=lifespan,
    title="TEMPSAFE API",
    description="Backend API for the TEMPSAFE temperature monitoring prototype.",
    version="0.1.0",
)

# Add /api to API routes; page routes keep their existing frontend URLs.
app.include_router(auth_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(boxes_router, prefix="/api")
app.include_router(configuration_router, prefix="/api")
app.include_router(readings_router, prefix="/api")
app.include_router(pages_router)

# Locate the frontend relative to this file, regardless of the working directory.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

# Serve assets at the paths already used by the HTML pages.
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
