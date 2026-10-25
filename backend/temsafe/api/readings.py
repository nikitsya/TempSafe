"""Routes for retrieving temperature readings."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from temsafe import models
from temsafe.database import get_db
from temsafe.schemas import ReadingResponse
from typing import Annotated

router = APIRouter(tags=["Readings"])


@router.get("/readings", response_model=list[ReadingResponse])
def get_readings(
        db: Annotated[Session, Depends(get_db)],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return the most recently received samples, with a maximum of 100 records."""
    # Sort by receipt time; delayed uploads may have older observation times.
    result = db.execute(
        select(models.TemperatureSample)
        .order_by(
            models.TemperatureSample.received_at.desc(),
            models.TemperatureSample.sample_id.desc(),
        )
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/readings/{sample_id}", response_model=ReadingResponse)
def get_reading(
        sample_id: str,
        db: Annotated[Session, Depends(get_db)]
):
    """Return one sample by ID, or 404 when it does not exist."""
    result = db.execute(
        select(models.TemperatureSample).where(models.TemperatureSample.sample_id == sample_id)
    )
    reading = result.scalars().first()

    if reading:
        return reading
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Temperature reading not found",
    )
