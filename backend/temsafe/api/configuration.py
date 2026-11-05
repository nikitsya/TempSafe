"""Operator-only routes for a box's desired configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated
from uuid import uuid4

from temsafe.admin import require_configuration_admin
from temsafe.api.auth import require_box
from temsafe.database import get_db
from temsafe.models import Box, BoxConfiguration, ThresholdProfile
from temsafe.schemas import HeartbeatSettings, ThresholdSettingsCreate, ThresholdSettingsResponse

router = APIRouter(tags=["Configuration"], dependencies=[Depends(require_box), Depends(require_configuration_admin)])


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


@router.get("/boxes/{box_id}/configuration/heartbeat", response_model=HeartbeatSettings)
def get_heartbeat_settings(box_id: str, db: Annotated[Session, Depends(get_db)]):
    """Read the desired interval even when the box has no threshold profile."""
    box = db.get(Box, box_id)
    if box is None:
        raise HTTPException(404, "Box not found")
    return HeartbeatSettings(heartbeat_interval_seconds=box.heartbeat_interval_seconds)


@router.put("/boxes/{box_id}/configuration/heartbeat", response_model=HeartbeatSettings)
def set_heartbeat_settings(box_id: str, settings: HeartbeatSettings, db: Annotated[Session, Depends(get_db)]):
    """Update the desired interval independently of device contact."""
    box = db.get(Box, box_id, with_for_update=True)
    if box is None:
        raise HTTPException(404, "Box not found")
    box.heartbeat_interval_seconds = settings.heartbeat_interval_seconds
    db.commit()
    return settings
