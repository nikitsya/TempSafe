"""Routes for retrieving box information."""

from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated

from temsafe.api.auth import require_box
from temsafe.db import models
from temsafe.db.session import get_db
from temsafe.monitoring.freshness import classify_freshness
from temsafe.monitoring.temperature import classify_temperature
from temsafe.schemas import BoxResponse, HistoryReadingResponse, LatestReadingResponse, ReadingResponse

router = APIRouter(tags=["Boxes"], dependencies=[Depends(require_box)])


def recorded_readings(box_id: str):
    """Join samples to their recorded profiles using the composite foreign key."""
    return (
        select(models.TemperatureSample, models.ThresholdProfile)
        .join(models.ThresholdProfile)
        .where(models.TemperatureSample.box_id == box_id)
        .order_by(models.TemperatureSample.sequence_no.desc())
    )


def history_reading(sample: models.TemperatureSample, profile: models.ThresholdProfile) -> HistoryReadingResponse:
    return HistoryReadingResponse(
        **ReadingResponse.model_validate(sample).model_dump(),
        temperature_state=classify_temperature(sample.temperature_c, sample.quality, profile),
        profile=profile,
    )


@router.get("/boxes/{box_id}/readings", response_model=list[HistoryReadingResponse])
def get_box_readings(
        box_id: str,
        db: Annotated[Session, Depends(get_db)],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return this box's history in descending measurement order."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))

    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    rows = db.execute(recorded_readings(box_id).limit(limit))
    return [history_reading(sample, profile) for sample, profile in rows]


@router.get("/boxes/{box_id}/readings/latest", response_model=LatestReadingResponse)
def get_latest_reading(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Return the last sample taken by this box, including sensor errors."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))
    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    row = db.execute(recorded_readings(box_id).limit(1)).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings available for this box",
        )

    sample = history_reading(*row)
    return LatestReadingResponse(
        **sample.model_dump(),
        freshness=classify_freshness(sample.observed_at, sample.clock_reliable, datetime.now(UTC)),
    )


@router.get("/boxes/{box_id}", response_model=BoxResponse)
def get_box(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Return one box by ID, or 404 when it does not exist."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))
    box = result.scalars().first()

    if box:
        return box
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Box not found",
    )
