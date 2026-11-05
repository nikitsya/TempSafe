"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from temsafe.api.boxes import router as boxes_router
from temsafe.api.configuration import router as configuration_router
from temsafe.api.health import router as health_router
from temsafe.api.readings import router as readings_router
from temsafe.pages import router as pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run the local MQTT subscriber alongside the API."""
    if os.getenv("TEMSAFE_LOCAL_MQTT") != "1":
        yield
        return

    from temsafe.mqtt_worker import build_client

    client = build_client()
    client.connect_async("mosquitto", 1883)
    client.loop_start()
    try:
        yield
    finally:
        client.disconnect()
        client.loop_stop()


# Create the application and set the information shown in the API documentation.
app = FastAPI(
    lifespan=lifespan,
    title="TEMSAFE API",
    description="Backend API for the TEMSAFE temperature monitoring prototype.",
    version="0.1.0",
)

# Add /api to API routes; page routes keep their existing frontend URLs.
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
