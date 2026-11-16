"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from tempsafe.api.auth import router as auth_router
from tempsafe.api.boxes import router as boxes_router
from tempsafe.api.configuration import router as configuration_router
from tempsafe.api.health import router as health_router
from tempsafe.api.readings import router as readings_router
from tempsafe.db.session import engine
from tempsafe.mqtt import create_mqtt
from tempsafe.pages import router as pages_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Run the MQTT subscriber and release the MySQL pool when the API stops."""
    mqtt = None
    try:
        mqtt = create_mqtt()
        if mqtt is not None:
            await asyncio.wait_for(mqtt.mqtt_startup(), timeout=15)
        yield
    finally:
        try:
            if mqtt is not None:
                await mqtt.mqtt_shutdown()
        finally:
            await engine.dispose()


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
