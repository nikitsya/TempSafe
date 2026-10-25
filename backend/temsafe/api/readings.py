"""Routes for retrieving temperature readings."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from temsafe import models
from temsafe.database import get_db
from temsafe.schemas import ReadingResponse

router = APIRouter(tags=["Readings"])


@router.get("/readings/{sample_id}", response_model=ReadingResponse)
def get_reading(sample_id: str, db: Annotated[Session, Depends(get_db)]):
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
