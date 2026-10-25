"""Check incoming validation and storage against the existing MySQL schema."""

import pytest
from datetime import datetime
from mysql.connector.errors import IntegrityError as MySQLIntegrityError
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from temsafe.database import SessionLocal
from temsafe.models import Box, TemperatureSample, ThresholdProfile
from temsafe.readings import save_reading
from temsafe.schemas import ReadingCreate
from uuid import uuid4


@pytest.fixture
def payload():
    """Provide a valid device payload without inserting any records."""
    return {
        "sample_id": str(uuid4()), "box_id": f"pytest-{uuid4()}",
        "sequence_no": 1, "profile_id": str(uuid4()),
        "observed_at": "2026-01-01T13:00:00+01:00", "clock_reliable": True,
        "temperature_c": "24.50", "quality": "valid",
    }


@pytest.fixture
def stored_box(payload):
    """Commit only test parents, then remove this test's samples and parents."""
    with SessionLocal() as db:
        try:
            db.add(Box(box_id=payload["box_id"], name="Reading storage test"))
            db.flush()
            db.add(ThresholdProfile(
                profile_id=payload["profile_id"], box_id=payload["box_id"],
                lower_c=0, warning_c=24, upper_c=25,
                source_note="Synthetic profile for storage tests.", is_demo=True,
            ))
            db.commit()
            yield payload
        finally:
            db.rollback()
            db.execute(delete(TemperatureSample).where(TemperatureSample.box_id == payload["box_id"]))
            db.execute(delete(ThresholdProfile).where(ThresholdProfile.box_id == payload["box_id"]))
            db.execute(delete(Box).where(Box.box_id == payload["box_id"]))
            db.commit()


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
])
def test_invalid_payload_is_rejected(payload, changes):
    """Reject invalid data before opening a database session."""
    with pytest.raises(ValidationError):
        ReadingCreate(**(payload | changes))


def test_save_and_identical_retry(stored_box):
    """Commit a sample, then accept an equivalent retry in another session."""
    with SessionLocal() as db:
        saved = save_reading(db, ReadingCreate(**stored_box))
        assert saved.observed_at == datetime(2026, 1, 1, 12)
        received_at = saved.received_at

    # Different offsets representing the same instant are the same observation.
    retry = stored_box | {"observed_at": "2026-01-01T12:00:00Z"}

    with SessionLocal() as db:
        saved = save_reading(db, ReadingCreate(**retry))
        assert saved.sample_id == stored_box["sample_id"]
        assert saved.received_at == received_at

        count = db.scalar(select(func.count()).select_from(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        ))
        assert count == 1
        assert db.get(Box, stored_box["box_id"]).last_seen_at is None


@pytest.mark.parametrize("changes", [
    {"temperature_c": "24.00"},
    {"sequence_no": 2},
    {"sample_id": "6ddf0f28-bec1-4d74-a320-51d095156dec"},
    {"observed_at": "2026-01-01T12:01:00Z"},
    {"quality": "sensor_error", "temperature_c": None},
])
def test_conflicting_retry_preserves_original(stored_box, changes):
    """Reject changed payloads and new IDs reusing the same box sequence."""
    with SessionLocal() as db:
        save_reading(db, ReadingCreate(**stored_box))

    with SessionLocal() as db:
        with pytest.raises(ValueError, match="conflicts"):
            save_reading(db, ReadingCreate(**(stored_box | changes)))

    with SessionLocal() as db:
        rows = db.scalars(select(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        )).all()

        assert len(rows) == 1
        assert rows[0].sample_id == stored_box["sample_id"]
        assert str(rows[0].temperature_c) == "24.50"
        assert rows[0].sequence_no == 1


@pytest.mark.parametrize("case", ["missing_box", "missing_profile", "wrong_box"])
def test_parent_records_are_required(stored_box, case):
    """Require an existing box and a profile owned by that box."""
    data = stored_box.copy()

    with SessionLocal() as db:
        other_box_id = f"pytest-{uuid4()}"

        try:
            if case == "missing_box":
                data["box_id"] = other_box_id
            elif case == "missing_profile":
                data["profile_id"] = str(uuid4())
            else:
                db.add(Box(box_id=other_box_id, name="Other test box"))
                db.commit()
                data["box_id"] = other_box_id
            with pytest.raises(ValueError, match="not found"):
                save_reading(db, ReadingCreate(**data))
            assert db.get(TemperatureSample, data["sample_id"]) is None

        finally:
            db.rollback()
            db.execute(delete(Box).where(Box.box_id == other_box_id))
            db.commit()


@pytest.mark.parametrize("changes", [
    {"quality": "sensor_error", "temperature_c": None},
    {"clock_reliable": False, "observed_at": None},
])
def test_error_and_unreliable_clock_samples_are_saved(stored_box, changes):
    """Preserve sensor failures and unknown observation times in history."""
    data = ReadingCreate(**(stored_box | changes))

    with SessionLocal() as db:
        saved = save_reading(db, data)
        assert saved.quality == data.quality
        assert saved.temperature_c == data.temperature_c
        assert saved.clock_reliable == data.clock_reliable
        if not data.clock_reliable:
            assert saved.observed_at is None


@pytest.mark.parametrize("conflicting", [False, True])
def test_duplicate_insert_race(stored_box, monkeypatch, conflicting):
    """Simulate another worker committing between our lookup and insert."""
    with SessionLocal() as db:
        def competing_commit():
            winner = stored_box | ({"temperature_c": "23.00"} if conflicting else {})
            with SessionLocal() as other_db:
                save_reading(other_db, ReadingCreate(**winner))
            raise IntegrityError("INSERT", {}, MySQLIntegrityError("Duplicate entry", errno=1062))

        monkeypatch.setattr(db, "commit", competing_commit)

        if conflicting:
            with pytest.raises(ValueError, match="conflicts"):
                save_reading(db, ReadingCreate(**stored_box))
        else:
            saved = save_reading(db, ReadingCreate(**stored_box))
            assert saved.sample_id == stored_box["sample_id"]

        assert db.scalar(select(func.count()).select_from(TemperatureSample).where(
            TemperatureSample.box_id == stored_box["box_id"]
        )) == 1
