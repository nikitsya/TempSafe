"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from temsafe.api.health import router as health_router
from temsafe.pages import router as pages_router

# Create the application and set the information shown in the API documentation.
app = FastAPI(
    title="TEMSAFE API",
    description="Backend API for the TEMSAFE temperature monitoring prototype.",
    version="0.1.0",
)

# Add /api to the health route; page routes keep their existing frontend URLs.
app.include_router(health_router, prefix="/api")
app.include_router(pages_router)

# Locate the frontend relative to this file, regardless of the working directory.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

# Serve assets at the paths already used by the HTML pages.
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
