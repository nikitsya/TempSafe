"""Manage the desired configuration of an assigned box."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tempsafe.api.auth import require_box
from tempsafe.db.models import Box, BoxConfiguration, ThresholdProfile
from tempsafe.db.session import get_db
from tempsafe.schemas import ThresholdSettingsCreate, ThresholdSettingsResponse

router = APIRouter(tags=["Configuration"], dependencies=[Depends(require_box)])


@router.get("/boxes/{box_id}/configuration", response_model=ThresholdSettingsResponse)
async def get_configuration(box_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Return the explicitly selected profile; never infer it from sample order."""
    if await db.get(Box, box_id) is None:
        raise HTTPException(404, "Box not found")
    configuration = await db.get(BoxConfiguration, box_id)
    if configuration is None:
        raise HTTPException(404, "No threshold configuration selected")
    return await db.get(ThresholdProfile, configuration.profile_id)


@router.put("/boxes/{box_id}/configuration", response_model=ThresholdSettingsResponse)
async def set_configuration(
        box_id: str,
        settings: ThresholdSettingsCreate,
        db: Annotated[AsyncSession, Depends(get_db)],
):
    """Atomically create a profile and select it; serialise writes per box."""
    try:
        box = await db.scalar(select(Box).where(Box.box_id == box_id).with_for_update())
        if box is None:
            raise HTTPException(404, "Box not found")
        configuration = await db.get(BoxConfiguration, box_id)
        current = await db.get(ThresholdProfile, configuration.profile_id) if configuration else None
        # A retry with unchanged values must not create another profile.
        if current and all(getattr(current, key) == value for key, value in settings.model_dump().items()):
            response = ThresholdSettingsResponse.model_validate(current)
            await db.commit()
            return response
        profile = ThresholdProfile(
            profile_id=str(uuid4()), box_id=box_id, is_demo=True, **settings.model_dump()
        )
        db.add(profile)
        await db.flush()
        if configuration is None:
            db.add(BoxConfiguration(box_id=box_id, profile_id=profile.profile_id))
        else:
            configuration.profile_id = profile.profile_id
        await db.flush()
        await db.refresh(profile)
        response = ThresholdSettingsResponse.model_validate(profile)
        await db.commit()
        return response
    except Exception:
        await db.rollback()
        raise
