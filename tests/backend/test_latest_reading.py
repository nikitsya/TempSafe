"""Check latest readings and box history against MySQL using temporary records."""

import pytest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from temsafe.database import SessionLocal, get_db
from temsafe.main import app
from temsafe.models import Box, TemperatureSample, ThresholdProfile
from unittest.mock import Mock
from uuid import uuid4


@pytest.fixture
def latest_reading_data(monkeypatch, grant_boxes):
    """Share one uncommitted session with the endpoint and roll it back afterwards."""
    clock = Mock()
    clock.now.return_value = datetime(2026, 1, 1, 12, 10, tzinfo=UTC)
    monkeypatch.setattr("temsafe.api.boxes.datetime", clock)
    with SessionLocal() as db:
        box_ids = [f"pytest-{uuid4()}", f"pytest-{uuid4()}"]
        grant_boxes(*box_ids)
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
                    created_at=datetime(2026, 1, 1),
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
    assert reading["temperature_state"] == ("Normal" if quality == "valid" else "Unknown")
    assert reading["profile"] == {
        "profile_id": profile_ids[0],
        "lower_c": "2.00",
        "warning_c": "7.00",
        "upper_c": "8.00",
    }


@pytest.mark.parametrize("temperature, expected", [
    ("2.00", "Alert"),
    ("5.00", "Normal"),
    ("7.00", "Warning"),
    ("8.00", "Warning"),
    ("8.01", "Alert"),
])
def test_latest_state_uses_recorded_profile(latest_reading_data, temperature, expected):
    """Keep using the sample's 2/7/8 test profile after a different profile is added."""
    client, db, box_ids, profile_ids = latest_reading_data
    sample_id = str(uuid4())
    db.add(TemperatureSample(
        sample_id=sample_id, box_id=box_ids[0], profile_id=profile_ids[0],
        sequence_no=1, observed_at=datetime(2026, 1, 1, 12),
        received_at=datetime(2026, 1, 1, 12, 1), clock_reliable=True,
        quality="valid", temperature_c=Decimal(temperature),
    ))
    db.flush()
    # Adding another profile must not reinterpret an existing measurement.
    db.add(ThresholdProfile(
        profile_id=str(uuid4()), box_id=box_ids[0],
        lower_c=Decimal("0.00"), warning_c=Decimal("24.00"),
        upper_c=Decimal("25.00"), is_demo=True,
        source_note="Alternative profile for the API test only.",
        created_at=datetime(2026, 1, 2),
    ))
    db.flush()

    response = client.get(f"/api/boxes/{box_ids[0]}/readings/latest")
    assert response.status_code == 200
    assert response.json() == {
        "sample_id": sample_id,
        "box_id": box_ids[0],
        "sequence_no": 1,
        "profile_id": profile_ids[0],
        "observed_at": "2026-01-01T12:00:00Z",
        "clock_reliable": True,
        "received_at": "2026-01-01T12:01:00Z",
        "temperature_c": temperature,
        "quality": "valid",
        "temperature_state": expected,
        "freshness": "stale",
        "profile": {
            "profile_id": profile_ids[0],
            "lower_c": "2.00",
            "warning_c": "7.00",
            "upper_c": "8.00",
        },
    }


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
    assert readings[0]["temperature_state"] == "Unknown"
    assert readings[0]["temperature_c"] is None
    assert readings[0]["observed_at"] is None
    assert readings[0]["received_at"].endswith("Z")
    assert readings[1]["observed_at"] == "2026-01-01T12:01:00Z"


def test_box_history_uses_each_recorded_profile(latest_reading_data):
    client, db, box_ids, profile_ids = latest_reading_data
    new_id = str(uuid4())
    db.add(ThresholdProfile(
        profile_id=new_id, box_id=box_ids[0], lower_c=Decimal("0.00"),
        warning_c=Decimal("24.00"), upper_c=Decimal("25.00"),
        source_note="Second test profile.",
    ))
    db.flush()
    for sequence, profile_id in enumerate([profile_ids[0], new_id], start=1):
        db.add(TemperatureSample(
            sample_id=str(uuid4()), box_id=box_ids[0], sequence_no=sequence,
            profile_id=profile_id, clock_reliable=False, temperature_c=Decimal("7.50"),
            quality="valid",
        ))
    db.flush()

    response = client.get(f"/api/boxes/{box_ids[0]}/readings")
    assert response.status_code == 200
    assert [
               (row["profile"]["profile_id"], row["profile"]["warning_c"], row["temperature_state"])
               for row in response.json()
           ] == [(new_id, "24.00", "Normal"), (profile_ids[0], "7.00", "Warning")]


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


@pytest.mark.parametrize("quality", ["valid", "sensor_error"])
@pytest.mark.parametrize("age_seconds, expected", [
    (0, "fresh"),
    (89.999999, "fresh"),
    (90, "fresh"),
    (90.000001, "stale"),
    (300, "stale"),
    (-1, "unknown"),
    (None, "unknown"),
])
def test_latest_freshness_uses_observation_time(latest_reading_data, quality, age_seconds, expected):
    """Fresh uploads cannot refresh old observations or hide sensor errors."""
    client, db, box_ids, profile_ids = latest_reading_data
    now = datetime(2026, 1, 1, 12, 10)
    observed_at = None if age_seconds is None else now - timedelta(seconds=age_seconds)
    db.add(TemperatureSample(
        sample_id=str(uuid4()), box_id=box_ids[0], profile_id=profile_ids[0],
        sequence_no=1, observed_at=observed_at, clock_reliable=observed_at is not None,
        received_at=now, quality=quality,
        temperature_c=Decimal("5.25") if quality == "valid" else None,
    ))
    db.flush()

    response = client.get(f"/api/boxes/{box_ids[0]}/readings/latest")

    assert response.status_code == 200
    reading = response.json()
    assert reading["freshness"] == expected
    assert reading["quality"] == quality
    assert reading["temperature_state"] == ("Normal" if quality == "valid" else "Unknown")
    assert reading["received_at"] == "2026-01-01T12:10:00Z"
