"""Check latest readings and box history against MySQL using temporary records."""

import pytest
from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from temsafe.database import SessionLocal, get_db
from temsafe.main import app
from temsafe.models import Box, TemperatureSample, ThresholdProfile
from uuid import uuid4


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


@pytest.mark.parametrize("query, expected_sequences", [
    ("", [102, 101, 100]),
    ("?limit=2", [102, 101]),
])
def test_box_history_order_and_limit(latest_reading_data, query, expected_sequences):
    """Return only this box's readings in measurement order, including errors."""
    client, db, box_ids, profile_ids = latest_reading_data

    # Insert out of sequence and give the oldest measurement the latest receipt time.
    for sequence, minute in [(101, 1), (102, 2), (100, 10)]:
        is_error = sequence == 102
        db.add(TemperatureSample(
            sample_id=str(uuid4()), box_id=box_ids[0], profile_id=profile_ids[0],
            sequence_no=sequence,
            observed_at=None if is_error else datetime(2026, 1, 1, 12, sequence - 100),
            received_at=datetime(2026, 1, 1, 12, minute),
            clock_reliable=not is_error,
            quality="sensor_error" if is_error else "valid",
            temperature_c=None if is_error else Decimal("5.25"),
        ))

    db.add(TemperatureSample(
        sample_id=str(uuid4()), box_id=box_ids[1], profile_id=profile_ids[1],
        sequence_no=999, observed_at=datetime(2026, 1, 1, 12, 20),
        received_at=datetime(2026, 1, 1, 12, 20), clock_reliable=True,
        quality="valid", temperature_c=Decimal("6.00"),
    ))
    db.flush()

    response = client.get(f"/api/boxes/{box_ids[0]}/readings{query}")
    assert response.status_code == 200

    readings = response.json()
    assert [row["sequence_no"] for row in readings] == expected_sequences
    assert all(row["box_id"] == box_ids[0] for row in readings)
    assert readings[0]["quality"] == "sensor_error"
    assert readings[0]["temperature_c"] is None
    assert readings[0]["observed_at"] is None


def test_box_history_without_samples(latest_reading_data):
    """A known box without measurements has an empty history, not a 404."""
    client, _, box_ids, _ = latest_reading_data
    response = client.get(f"/api/boxes/{box_ids[0]}/readings")

    assert response.status_code == 200
    assert response.json() == []


def test_box_history_for_missing_box(latest_reading_data):
    """An unknown box returns the same error as the box details route."""
    client, _, _, _ = latest_reading_data
    response = client.get(f"/api/boxes/pytest-{uuid4()}/readings")

    assert response.status_code == 404
    assert response.json() == {"detail": "Box not found"}


@pytest.mark.parametrize("limit", ["0", "101", "invalid"])
def test_box_history_rejects_invalid_limit(latest_reading_data, limit):
    """Accept only integer limits between 1 and 100."""
    client, _, box_ids, _ = latest_reading_data
    response = client.get(f"/api/boxes/{box_ids[0]}/readings?limit={limit}")

    assert response.status_code == 422
