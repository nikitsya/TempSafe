"""Store validated readings and recognise retries without overwriting samples."""

from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from tempsafe.db.models import Box, TemperatureSample, ThresholdProfile
from tempsafe.monitoring.freshness import classify_freshness
from tempsafe.monitoring.push import record_transition
from tempsafe.schemas import ReadingCreate


class ReadingReferenceNotFound(ValueError):
    """The box or its temperature profile does not exist."""


class ReadingConflict(ValueError):
    """An existing sample uses the supplied identifiers with different data."""


async def _find_existing(db: AsyncSession, values: dict):
    """Look for either of the two unique identifiers used by the SQL schema."""
    result = await db.execute(select(TemperatureSample).where(or_(
        TemperatureSample.sample_id == values["sample_id"],
        and_(
            TemperatureSample.box_id == values["box_id"],
            TemperatureSample.sequence_no == values["sequence_no"],
        ),
    )))

    return result.scalars().all()


def _matching_retry(existing: list[TemperatureSample], values: dict):
    """Accept only an identical payload, including its original sample ID."""
    if len(existing) == 1 and all(
            getattr(existing[0], field) == value for field, value in values.items()
    ):
        return existing[0]

    raise ReadingConflict("Sample ID or box sequence number conflicts with an existing reading")


async def save_reading(db: AsyncSession, reading: ReadingCreate) -> TemperatureSample:
    """Save one validated sample using a dedicated session, or return an identical retry.

    The caller must authenticate the device and authorise its box before calling.
    This function commits the session, so do not mix unrelated pending changes into it.
    """
    values = reading.model_dump(exclude={"schema_version"})
    values["sample_id"] = str(reading.sample_id)
    values["profile_id"] = str(reading.profile_id)

    if reading.observed_at is not None:
        # MySQL DATETIME has no timezone: store a UTC value and compare retries in UTC.
        observed_at = reading.observed_at.astimezone(UTC).replace(tzinfo=None)
        if observed_at.year < 1000:
            raise ValueError("Observation time is outside the MySQL DATETIME range")
        values["observed_at"] = observed_at

    received_at = datetime.now(UTC).replace(tzinfo=None)
    track_state = (reading.sensor_location == "inside" and reading.quality == "valid"
                   and classify_freshness(values["observed_at"], reading.clock_reliable, received_at) == "fresh")
    box_query = select(Box).where(Box.box_id == reading.box_id)
    if track_state:
        box_query = box_query.with_for_update()
    result = await db.execute(box_query)
    if result.scalars().first() is None:
        raise ReadingReferenceNotFound("Box not found")

    result = await db.execute(select(ThresholdProfile).where(
        ThresholdProfile.profile_id == values["profile_id"],
        ThresholdProfile.box_id == reading.box_id,
    ))
    profile = result.scalars().first()
    if profile is None:
        raise ReadingReferenceNotFound("Temperature profile not found for this box")

    existing = await _find_existing(db, values)
    if existing:
        return _matching_retry(existing, values)

    # Receipt time belongs to the server, not the device, and stays unchanged on retries.
    sample = TemperatureSample(**values, received_at=received_at)

    try:
        db.add(sample)
        if track_state:
            await db.flush()
            await record_transition(db, sample, profile)
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        # Another worker may have inserted the same identifiers after our lookup.
        if error.orig.args[:1] == (1062,):
            existing = await _find_existing(db, values)
            if existing:
                return _matching_retry(existing, values)
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise

    await db.refresh(sample)

    return sample
