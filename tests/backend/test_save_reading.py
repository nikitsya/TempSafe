"""Check incoming validation and storage against the existing MySQL schema."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, func, select

from tempsafe.db.models import Box, TemperatureSample, ThresholdProfile
from tempsafe.db.session import AsyncSessionLocal
from tempsafe.monitoring.readings import save_reading
from tempsafe.schemas import ReadingCreate

pytestmark = pytest.mark.anyio

DEVICE_KEY = uuid4().hex


@pytest.fixture
def device_client(client):
    client.headers["X-Device-Key"] = DEVICE_KEY
    return client


@pytest.fixture
def payload(monkeypatch, grant_boxes):
    """Provide a valid device payload without inserting any records."""
    box_id = f"pytest-{uuid4()}"
    grant_boxes(box_id)
    monkeypatch.setenv("TEMPSAFE_DEVICE_KEY", DEVICE_KEY)
    monkeypatch.setenv("TEMPSAFE_DEVICE_BOX_ID", box_id)
    return {
        "sample_id": str(uuid4()), "box_id": box_id,
        "sequence_no": 1, "profile_id": str(uuid4()),
        "observed_at": "2026-01-01T13:00:00+01:00", "clock_reliable": True,
        "temperature_c": "24.50", "quality": "valid",
    }


@pytest.fixture
async def stored_box(payload, app_lifespan):
    """Commit only test parents, then remove this test's samples and parents."""
    reading = ReadingCreate.model_validate(payload)
    async with AsyncSessionLocal() as db:
        try:
            db.add(Box(box_id=reading.box_id, name="Reading storage test"))
            await db.flush()
            db.add(ThresholdProfile(
                profile_id=str(reading.profile_id), box_id=reading.box_id,
                lower_c=Decimal("0"), warning_c=Decimal("24"), upper_c=Decimal("25"),
                source_note="Synthetic profile for storage tests.", is_demo=True,
            ))
            await db.commit()
            yield payload
        finally:
            await db.rollback()
            await db.execute(delete(TemperatureSample).where(TemperatureSample.box_id == reading.box_id))
            await db.execute(delete(ThresholdProfile).where(ThresholdProfile.box_id == reading.box_id))
            await db.execute(delete(Box).where(Box.box_id == reading.box_id))
            await db.commit()


@pytest.mark.parametrize("changes", [
    {"temperature_c": None},
    {"temperature_c": "80.01"},
    {"temperature_c": "-40.01"},
    {"temperature_c": "NaN"},
    {"temperature_c": "Infinity"},
    {"temperature_c": "24.501"},
    {"quality": "sensor_error"},
    {"quality": "invalid"},
    {"clock_reliable": False},
    {"observed_at": None},
    {"observed_at": "2026-01-01T12:00:00"},
    {"sequence_no": -1},
    {"sequence_no": True},
    {"sequence_no": 18446744073709551616},
    {"sample_id": "not-a-uuid"},
    {"profile_id": "not-a-uuid"},
    {"received_at": "2026-01-01T12:00:00Z"},
    {"schema_version": 2},
    {"sensor_location": "roof"},
    {"sensor_location": None},
])
def test_invalid_payload_is_rejected(payload, changes):
    """Reject invalid data before opening a database session."""
    with pytest.raises(ValidationError):
        ReadingCreate(**(payload | changes))


async def test_save_and_identical_retry(stored_box):
    """Commit a sample, then accept an equivalent retry in another session."""
    async with AsyncSessionLocal() as db:
        saved = await save_reading(db, ReadingCreate(**stored_box))
        assert saved.sensor_location == "inside"
        assert saved.observed_at == datetime(2026, 1, 1, 12)
        received_at = saved.received_at

    # Different offsets representing the same instant are the same observation.
    retry = stored_box | {"observed_at": "2026-01-01T12:00:00Z"}

    async with AsyncSessionLocal() as db:
        saved = await save_reading(db, ReadingCreate(**retry))
        assert saved.sample_id == stored_box["sample_id"]
        assert saved.received_at == received_at

        count = await db.scalar(select(func.count()).select_from(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        ))
        assert count == 1


async def test_outside_retry_and_shared_sequence(stored_box, device_client):
    outside = stored_box | {"sensor_location": "outside"}
    first = await device_client.post("/api/readings", json=outside)
    assert first.status_code == 200 and first.json()["sensor_location"] == "outside"
    assert (await device_client.post("/api/readings", json=outside)).json() == first.json()
    conflicting = stored_box | {"sample_id": str(uuid4())}
    assert (await device_client.post("/api/readings", json=conflicting)).status_code == 409
    inside = conflicting | {"sequence_no": 2}
    assert (await device_client.post("/api/readings", json=inside)).status_code == 200


@pytest.mark.parametrize("changes", [
    {"temperature_c": "24.00"},
    {"sequence_no": 2},
    {"sensor_location": "outside"},
    {"sample_id": "6ddf0f28-bec1-4d74-a320-51d095156dec"},
    {"observed_at": "2026-01-01T12:01:00Z"},
    {"quality": "sensor_error", "temperature_c": None},
])
async def test_conflicting_retry_preserves_original(stored_box, changes):
    """Reject changed payloads and new IDs reusing the same box sequence."""
    async with AsyncSessionLocal() as db:
        await save_reading(db, ReadingCreate(**stored_box))

    async with AsyncSessionLocal() as db:
        with pytest.raises(ValueError, match="conflicts"):
            await save_reading(db, ReadingCreate(**(stored_box | changes)))

    async with AsyncSessionLocal() as db:
        rows = (await db.scalars(select(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        ))).all()

        assert len(rows) == 1
        assert rows[0].sample_id == stored_box["sample_id"]
        assert str(rows[0].temperature_c) == "24.50"
        assert rows[0].sequence_no == 1


@pytest.mark.parametrize("case", ["missing_box", "missing_profile", "wrong_box"])
async def test_parent_records_are_required(stored_box, case):
    """Require an existing box and a profile owned by that box."""
    data = stored_box.copy()

    async with AsyncSessionLocal() as db:
        other_box_id = f"pytest-{uuid4()}"

        try:
            if case == "missing_box":
                data["box_id"] = other_box_id
            elif case == "missing_profile":
                data["profile_id"] = str(uuid4())
            else:
                db.add(Box(box_id=other_box_id, name="Other test box"))
                await db.commit()
                data["box_id"] = other_box_id
            with pytest.raises(ValueError, match="not found"):
                await save_reading(db, ReadingCreate(**data))
            assert await db.get(TemperatureSample, data["sample_id"]) is None

        finally:
            await db.rollback()
            await db.execute(delete(Box).where(Box.box_id == other_box_id))
            await db.commit()


@pytest.mark.parametrize("changes", [
    {"quality": "sensor_error", "temperature_c": None},
    {"clock_reliable": False, "observed_at": None},
])
async def test_error_and_unreliable_clock_samples_are_saved(stored_box, changes):
    """Preserve sensor failures and unknown observation times in history."""
    data = ReadingCreate(**(stored_box | changes))

    async with AsyncSessionLocal() as db:
        saved = await save_reading(db, data)
        assert saved.quality == data.quality
        assert saved.temperature_c == data.temperature_c
        assert saved.clock_reliable == data.clock_reliable
        if not data.clock_reliable:
            assert saved.observed_at is None


@pytest.mark.parametrize("conflicting", [False, True])
async def test_duplicate_insert_race(stored_box, monkeypatch, conflicting):
    """Simulate another worker committing between our lookup and insert."""
    async with AsyncSessionLocal() as db:
        commit = db.commit

        async def competing_commit():
            winner = stored_box | ({"temperature_c": "23.00"} if conflicting else {})
            async with AsyncSessionLocal() as other_db:
                await save_reading(other_db, ReadingCreate(**winner))
            await commit()

        monkeypatch.setattr(db, commit.__name__, competing_commit)

        if conflicting:
            with pytest.raises(ValueError, match="conflicts"):
                await save_reading(db, ReadingCreate(**stored_box))
        else:
            saved = await save_reading(db, ReadingCreate(**stored_box))
            assert saved.sample_id == stored_box["sample_id"]

        assert await db.scalar(select(func.count()).select_from(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        )) == 1


async def test_post_reading_and_retry(stored_box, device_client):
    """Persist through HTTP and return the same sample for an equivalent retry."""
    response = await device_client.post("/api/readings", json=stored_box)
    assert response.status_code == 200
    saved = response.json()
    assert saved["sample_id"] == stored_box["sample_id"]
    assert saved["observed_at"] == "2026-01-01T12:00:00Z"
    assert saved["temperature_c"] == "24.50"
    assert saved["received_at"].endswith("Z")
    retry = stored_box | {"observed_at": "2026-01-01T12:00:00Z"}
    response = await device_client.post("/api/readings", json=retry)
    assert response.status_code == 200
    assert response.json() == saved
    assert (await device_client.get(f"/api/readings/{saved['sample_id']}")).json() == saved

    async with AsyncSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        )) == 1


@pytest.mark.parametrize("changes", [
    {"temperature_c": "23.00"},
    {"sample_id": "6ddf0f28-bec1-4d74-a320-51d095156dec"},
])
async def test_post_conflicting_reading(stored_box, changes, device_client):
    """Return 409 for reused identifiers and preserve the stored reading."""
    original = await device_client.post("/api/readings", json=stored_box)
    assert original.status_code == 200
    response = await device_client.post("/api/readings", json=stored_box | changes)
    assert response.status_code == 409
    assert "conflicts" in response.json()["detail"]
    assert (await device_client.get(f"/api/readings/{stored_box['sample_id']}")).json() == original.json()


@pytest.mark.parametrize("field, detail", [
    ("box_id", "Device cannot submit readings for this box"),
    ("profile_id", "Temperature profile not found for this box"),
])
async def test_post_missing_reference(stored_box, field, detail, device_client):
    """Return 404 when a required parent record is missing."""
    response = await device_client.post("/api/readings", json=stored_box | {field: str(uuid4())})
    assert response.status_code == (403 if field == "box_id" else 404)
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("changes", [
    {"quality": "sensor_error", "temperature_c": None},
    {"clock_reliable": False, "observed_at": None},
])
async def test_post_missing_sensor_or_clock_data(stored_box, changes, device_client):
    """Preserve explicitly missing measurements and unreliable clock data."""
    response = await device_client.post("/api/readings", json=stored_box | changes)
    assert response.status_code == 200
    for field, value in changes.items():
        assert response.json()[field] == value


@pytest.mark.parametrize("changes", [
    {"temperature_c": None},
    {"sample_id": "invalid"},
    {"received_at": "2026-01-01T12:00:00Z"},
    {"observed_at": "0999-01-01T12:00:00Z"},
])
async def test_post_invalid_reading(payload, changes, device_client):
    """Return 422 for invalid payloads, including unsupported database dates."""
    response = await device_client.post("/api/readings", json=payload | changes)
    assert response.status_code == 422
