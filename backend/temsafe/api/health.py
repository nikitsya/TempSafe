"""Application liveness endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal

# Group this endpoint under Health in the interactive API documentation.
router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Define the response structure, allowing only 'ok' as the status value."""
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Confirm that the API is running, without checking external services."""
    return HealthResponse()
