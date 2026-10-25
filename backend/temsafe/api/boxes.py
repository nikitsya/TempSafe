"""Routes for retrieving box information."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from temsafe import models
from temsafe.database import get_db
from temsafe.schemas import BoxResponse, ReadingResponse
from typing import Annotated

router = APIRouter(tags=["Boxes"])


@router.get("/boxes/{box_id}/readings", response_model=list[ReadingResponse])
def get_box_readings(
        box_id: str,
        db: Annotated[Session, Depends(get_db)],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return this box's history in descending measurement order."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))

    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    # Keep sensor errors in the history and exclude readings from other boxes.
    result = db.execute(
        select(models.TemperatureSample)
        .where(models.TemperatureSample.box_id == box_id)
        .order_by(models.TemperatureSample.sequence_no.desc())
        .limit(limit)
    )

    return result.scalars().all()


@router.get("/boxes/{box_id}/readings/latest", response_model=ReadingResponse)
def get_latest_reading(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Return the last sample taken by this box, including sensor errors."""
    result = db.execute(select(models.Box).where(models.Box.box_id == box_id))
    if result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    # Sequence numbers describe measurement order within one box, not upload order.
    result = db.execute(
        select(models.TemperatureSample)
        .where(models.TemperatureSample.box_id == box_id)
        .order_by(models.TemperatureSample.sequence_no.desc())
        .limit(1)
    )

    reading = result.scalars().first()

    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No readings available for this box",
        )

    return reading


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
