"""Application liveness endpoint."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Confirm that the API is running, without checking external services."""
    return HealthResponse()
