"""Check measurement ordering against MySQL using temporary test records."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from temsafe.database import SessionLocal, get_db
from temsafe.main import app
from temsafe.models import Box, TemperatureSample, ThresholdProfile


@pytest.fixture
def latest_reading_data():
    """Share one uncommitted session with the endpoint and roll it back afterwards."""
    with SessionLocal() as db:
        box_ids = [f"pytest-{uuid4()}", f"pytest-{uuid4()}"]
        profile_ids = [str(uuid4()), str(uuid4())]

        try:
            for box_id, profile_id in zip(box_ids, profile_ids):
                db.add(Box(box_id=box_id, name="Latest reading test box"))
                db.flush()
                db.add(ThresholdProfile(
                    profile_id=profile_id, box_id=box_id,
                    lower_c=Decimal("2.00"), warning_c=Decimal("7.00"),
                    upper_c=Decimal("8.00"), is_demo=True,
                    source_note="Synthetic limits for tests only.",
                ))
                db.flush()

            def override_get_db():
                yield db

            app.dependency_overrides[get_db] = override_get_db
            with TestClient(app) as client:
                yield client, db, box_ids, profile_ids
        finally:
            app.dependency_overrides.pop(get_db, None)
            db.rollback()


@pytest.mark.parametrize("quality", ["valid", "sensor_error"])
def test_latest_reading_uses_box_sequence(latest_reading_data, quality):
    """Ignore a delayed older upload and another box's higher sequence number."""
    client, db, box_ids, profile_ids = latest_reading_data
    latest_id = str(uuid4())

    # The newest measurement arrives first; an older measurement is uploaded later.
    db.add(TemperatureSample(
        sample_id=latest_id, box_id=box_ids[0], profile_id=profile_ids[0],
        sequence_no=101, observed_at=datetime(2026, 1, 1, 12, 1),
        received_at=datetime(2026, 1, 1, 12, 1), clock_reliable=True,
        quality=quality, temperature_c=Decimal("5.25") if quality == "valid" else None,
    ))
    db.flush()
    db.add(TemperatureSample(
        sample_id=str(uuid4()), box_id=box_ids[0], profile_id=profile_ids[0],
        sequence_no=100, observed_at=datetime(2026, 1, 1, 12),
        received_at=datetime(2026, 1, 1, 12, 10), clock_reliable=True,
        quality="valid", temperature_c=Decimal("4.00"),
    ))
    db.add(TemperatureSample(
        sample_id=str(uuid4()), box_id=box_ids[1], profile_id=profile_ids[1],
        sequence_no=999, observed_at=datetime(2026, 1, 1, 12, 20),
        received_at=datetime(2026, 1, 1, 12, 20), clock_reliable=True,
        quality="valid", temperature_c=Decimal("6.00"),
    ))
    db.flush()

    response = client.get(f"/api/boxes/{box_ids[0]}/readings/latest")

    assert response.status_code == 200
    reading = response.json()

    assert reading["sample_id"] == latest_id
    assert reading["box_id"] == box_ids[0]
    assert reading["sequence_no"] == 101
    assert reading["quality"] == quality
    assert reading["temperature_c"] == ("5.25" if quality == "valid" else None)


def test_latest_reading_without_samples(latest_reading_data):
    """Explain that a known box has no recorded measurements yet."""
    client, _, box_ids, _ = latest_reading_data
    response = client.get(f"/api/boxes/{box_ids[0]}/readings/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "No readings available for this box"}


def test_latest_reading_for_missing_box(latest_reading_data):
    """Distinguish an unknown box from a known box without measurements."""
    client, _, _, _ = latest_reading_data
    response = client.get(f"/api/boxes/pytest-{uuid4()}/readings/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "Box not found"}
