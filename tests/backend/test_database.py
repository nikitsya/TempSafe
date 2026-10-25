"""Check the real MySQL connection using the project's .env settings.

Start the configured MySQL server before running this test.
"""

from datetime import datetime
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from temsafe.database import SessionLocal, get_db
from temsafe.main import app
from temsafe.models import Box, TemperatureSample, ThresholdProfile
from uuid import uuid4


def test_database_connection():
    """Confirm that a backend session can execute a query in MySQL."""
    dependency = get_db()
    session = next(dependency)

    try:
        # SELECT 1 checks the connection without changing any stored data.
        result = session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1
    finally:
        dependency.close()


def test_measurement_is_written_and_read_back():
    """Commit one measurement, read it in a new session and remove the test data."""

    box_id = f"pytest-{uuid4()}"
    profile_id = str(uuid4())
    sample_id = str(uuid4())
    observed_at = datetime(2026, 1, 1, 12, 0, 0)

    try:
        with SessionLocal() as db:
            box = Box(box_id=box_id, name="Pytest measurement box")
            db.add(box)

            # Write the parent row before inserting rows that reference it.
            db.flush()

            profile = ThresholdProfile(
                profile_id=profile_id,
                box_id=box_id,
                lower_c=Decimal("2.00"),
                upper_c=Decimal("8.00"),
                warning_c=Decimal("7.00"),
                source_note="Synthetic limits for the database test only.",
                is_demo=True,
            )

            db.add(profile)
            db.flush()

            measurement = TemperatureSample(
                sample_id=sample_id,
                box_id=box_id,
                sequence_no=1,
                profile_id=profile_id,
                observed_at=observed_at,
                clock_reliable=True,
                temperature_c=Decimal("5.25"),
                quality="valid",
            )

            db.add(measurement)
            db.commit()
            db.refresh(measurement)

            assert measurement.received_at is not None

        # A new session confirms that the committed row can be read from MySQL.
        with SessionLocal() as db:
            result = db.execute(
                select(TemperatureSample).where(TemperatureSample.sample_id == sample_id)
            )

            saved_measurement = result.scalars().one()

            assert saved_measurement.temperature_c == Decimal("5.25")
            assert saved_measurement.box_id == box_id
            assert saved_measurement.profile_id == profile_id
            assert saved_measurement.sequence_no == 1
            assert saved_measurement.observed_at == observed_at
            assert saved_measurement.clock_reliable is True
            assert saved_measurement.quality == "valid"

        # Check the same committed measurement through the HTTP endpoint.
        with TestClient(app) as client:
            response = client.get(f"/api/readings/{sample_id}")
        assert response.status_code == 200
        assert response.json() == {
            "sample_id": sample_id,
            "box_id": box_id,
            "sequence_no": 1,
            "profile_id": profile_id,
            "observed_at": observed_at.isoformat(),
            "clock_reliable": True,
            "received_at": saved_measurement.received_at.isoformat(),
            "temperature_c": "5.25",
            "quality": "valid",
        }

    finally:
        # Remove only this run's records, children first to respect foreign keys.
        # This also runs if an assertion fails after the transaction was committed.
        with SessionLocal() as db:
            for model, record_id in (
                    (TemperatureSample, sample_id),
                    (ThresholdProfile, profile_id),
                    (Box, box_id),
            ):
                record = db.get(model, record_id)
                if record is not None:
                    db.delete(record)
                    db.flush()
            db.commit()


def test_missing_reading_returns_404():
    """Return a clear HTTP error when the requested sample does not exist."""
    with TestClient(app) as client:
        response = client.get(f"/api/readings/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Temperature reading not found"}
