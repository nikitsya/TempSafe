"""Routes for storing and retrieving temperature readings."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated

from temsafe.api.auth import AllowedBoxes, require_device
from temsafe.db import models
from temsafe.db.session import get_db
from temsafe.monitoring.readings import ReadingConflict, ReadingReferenceNotFound, save_reading
from temsafe.schemas import ReadingCreate, ReadingResponse

router = APIRouter(tags=["Readings"])


@router.post("/readings", response_model=ReadingResponse, responses={
    404: {"description": "Box or temperature profile not found"},
    409: {"description": "Sample identifiers conflict with an existing reading"},
})
def post_reading(
        reading: ReadingCreate,
        device_box: Annotated[str, Depends(require_device)],
        db: Annotated[Session, Depends(get_db)],
):
    """Store a sample or return an identical retry without changing its receipt time."""
    if reading.box_id != device_box:
        raise HTTPException(403, "Device cannot submit readings for this box")
    try:
        return save_reading(db, reading)
    except ReadingReferenceNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ReadingConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error


@router.get("/readings", response_model=list[ReadingResponse])
def get_readings(
        allowed: AllowedBoxes,
        db: Annotated[Session, Depends(get_db)],
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return the most recently received samples, with a maximum of 100 records."""
    # Sort by receipt time; delayed uploads may have older observation times.
    result = db.execute(
        select(models.TemperatureSample)
        .where(models.TemperatureSample.box_id.in_(allowed))
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
        allowed: AllowedBoxes,
        db: Annotated[Session, Depends(get_db)]
):
    """Return one sample by ID, or 404 when it does not exist."""
    result = db.execute(
        select(models.TemperatureSample).where(
            models.TemperatureSample.sample_id == sample_id, models.TemperatureSample.box_id.in_(allowed)
        )
    )
    reading = result.scalars().first()

    if reading:
        return reading
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Temperature reading not found",
    )
