"""Manage the desired configuration of an assigned box."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from tempsafe.api.auth import require_box
from tempsafe.db.models import Box, BoxConfiguration, ThresholdProfile
from tempsafe.db.session import get_db
from tempsafe.schemas import ThresholdSettingsCreate, ThresholdSettingsResponse

router = APIRouter(tags=["Configuration"], dependencies=[Depends(require_box)])


@router.get("/boxes/{box_id}/configuration", response_model=ThresholdSettingsResponse)
def get_configuration(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Return the explicitly selected profile; never infer it from sample order."""
    if db.get(Box, box_id) is None:
        raise HTTPException(404, "Box not found")
    configuration = db.get(BoxConfiguration, box_id)
    if configuration is None:
        raise HTTPException(404, "No threshold configuration selected")
    return db.get(ThresholdProfile, configuration.profile_id)


@router.put("/boxes/{box_id}/configuration", response_model=ThresholdSettingsResponse)
def set_configuration(
        box_id: str,
        settings: ThresholdSettingsCreate,
        db: Annotated[Session, Depends(get_db)],
):
    """Atomically create a profile and select it; serialise writes per box."""
    try:
        box = db.execute(select(Box).where(Box.box_id == box_id).with_for_update()).scalar_one_or_none()
        if box is None:
            raise HTTPException(404, "Box not found")
        configuration = db.get(BoxConfiguration, box_id)
        current = db.get(ThresholdProfile, configuration.profile_id) if configuration else None
        # A retry with unchanged values must not create another profile.
        if current and all(getattr(current, key) == value for key, value in settings.model_dump().items()):
            response = ThresholdSettingsResponse.model_validate(current)
            db.commit()
            return response
        profile = ThresholdProfile(
            profile_id=str(uuid4()), box_id=box_id, is_demo=True, **settings.model_dump()
        )
        db.add(profile)
        db.flush()
        if configuration is None:
            db.add(BoxConfiguration(box_id=box_id, profile_id=profile.profile_id))
        else:
            configuration.profile_id = profile.profile_id
        db.flush()
        response = ThresholdSettingsResponse.model_validate(profile)
        db.commit()
        return response
    except Exception:
        db.rollback()
        raise
