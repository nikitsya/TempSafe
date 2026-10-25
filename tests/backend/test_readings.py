"""Check the reading list's HTTP responses without requiring a MySQL server."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from temsafe.database import get_db
from temsafe.main import app
from temsafe.models import TemperatureSample


@pytest.fixture
def reading_client():
    """Replace the database session for these HTTP response tests only."""
    db = Mock()
    db.execute.return_value.scalars.return_value.all.return_value = []

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        del app.dependency_overrides[get_db]


def test_readings_list_returns_sample(reading_client):
    """Serialise a stored sample as an item in a JSON list."""
    client, db = reading_client
    sample = TemperatureSample(
        sample_id="test-sample", box_id="test-box", sequence_no=1,
        profile_id="test-profile", observed_at=None, clock_reliable=False,
        received_at=datetime(2026, 1, 1, 12), temperature_c=Decimal("5.25"),
        quality="valid",
    )
    db.execute.return_value.scalars.return_value.all.return_value = [sample]
    response = client.get("/api/readings?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sample_id"] == "test-sample"
    assert response.json()[0]["temperature_c"] == "5.25"
    assert response.json()[0]["observed_at"] is None


def test_readings_list_can_be_empty(reading_client):
    """Return an empty list rather than 404 when no samples are available."""
    client, _ = reading_client
    response = client.get("/api/readings")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("limit", ["0", "101", "invalid"])
def test_readings_rejects_invalid_limit(reading_client, limit):
    """Reject invalid limits before executing a query."""
    client, db = reading_client
    response = client.get(f"/api/readings?limit={limit}")
    assert response.status_code == 422
    db.execute.assert_not_called()
