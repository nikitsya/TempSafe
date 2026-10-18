"""FastAPI application entry point."""

from fastapi import FastAPI

from temsafe.api.health import router as health_router

app = FastAPI(
    title="TEMSAFE API",
    description="Backend API for the TEMSAFE temperature monitoring prototype.",
    version="0.1.0",
)
app.include_router(health_router, prefix="/api")
