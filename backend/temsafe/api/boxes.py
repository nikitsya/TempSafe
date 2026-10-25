"""Routes for retrieving box information."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from temsafe import models
from temsafe.database import get_db
from temsafe.schemas import BoxResponse

router = APIRouter(tags=["Boxes"])


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
