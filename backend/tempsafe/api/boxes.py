"""Routes for retrieving box information."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tempsafe.api.auth import require_box
from tempsafe.db import models
from tempsafe.db.session import get_db
from tempsafe.monitoring.freshness import classify_freshness
from tempsafe.monitoring.temperature import classify_temperature
from tempsafe.schemas import BoxStatusResponse, as_utc, BoxResponse, HistoryReadingResponse, LatestReadingResponse, \
    ReadingResponse

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
    start_date: date | None = None,
    end_date: date | None = None,
    before_sequence: Annotated[int | None, Query(ge=0, le=18446744073709551615)] = None,
):
    """Return this box's history in descending measurement order."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))

    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    query = recorded_readings(box_id)
    sample = models.TemperatureSample
    if (start_date is None) != (end_date is None):
        raise HTTPException(422, "Supply both start_date and end_date")
    if start_date is not None:
        if start_date > end_date or start_date.year < 1001 or end_date == date.max:
            raise HTTPException(422, "Invalid history date range")
        dublin = ZoneInfo("Europe/Dublin")
        start = datetime.combine(start_date, time.min, dublin)
        stop = datetime.combine(end_date + timedelta(days=1), time.min, dublin)
        query = query.where(
            sample.observed_at >= start.astimezone(UTC).replace(tzinfo=None),
            sample.observed_at < stop.astimezone(UTC).replace(tzinfo=None),
        )
    if before_sequence is not None:
        query = query.where(sample.sequence_no < before_sequence)
    rows = db.execute(query.limit(limit))
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


@router.get("/boxes/{box_id}/status", response_model=BoxStatusResponse)
def get_box_status(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Use every stored receipt for contact and the latest valid sample for temperature."""
    sample = models.TemperatureSample
    receipt = select(func.max(sample.received_at)).where(sample.box_id == box_id)
    observation = (
        select(sample.observed_at)
        .where(sample.box_id == box_id, sample.quality == "valid")
        .order_by(sample.sequence_no.desc())
        .limit(1)
    )
    row = db.execute(
        select(receipt.scalar_subquery(), observation.scalar_subquery())
        .select_from(models.Box).where(models.Box.box_id == box_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(404, "Box not found")

    received, observed = row
    now = datetime.now(UTC)
    last_received_at = as_utc(received) if received is not None else None
    observed_at = as_utc(observed) if observed is not None else None
    contact_status = "never_reported"
    if last_received_at is not None:
        contact_status = "not_reporting" if now - last_received_at > timedelta(seconds=90) else "reporting"
    return BoxStatusResponse(
        last_received_at=last_received_at,
        contact_status=contact_status,
        observed_at=observed_at,
        freshness=classify_freshness(observed_at, observed_at is not None, now),
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
