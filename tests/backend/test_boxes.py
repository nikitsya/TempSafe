"""Check box responses using a substituted database session."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from temsafe.database import get_db
from temsafe.main import app
from temsafe.models import Box


@pytest.fixture
def box_client():
    """Provide a test client without querying the real database."""
    db = Mock()
    db.execute.return_value.scalars.return_value.first.return_value = None

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        del app.dependency_overrides[get_db]


@pytest.mark.parametrize("last_seen_at", [None, datetime(2026, 1, 1, 12)])
def test_get_box_returns_details(box_client, last_seen_at):
    """Return both known and missing contact times in the expected JSON format."""
    client, db = box_client
    db.execute.return_value.scalars.return_value.first.return_value = Box(
        box_id="test-box", name="Test box", last_seen_at=last_seen_at
    )
    response = client.get("/api/boxes/test-box")
    assert response.status_code == 200
    assert response.json() == {
        "box_id": "test-box",
        "name": "Test box",
        "last_seen_at": last_seen_at.isoformat() if last_seen_at else None,
    }


def test_get_box_returns_404(box_client):
    """Report a missing box without returning an empty success response."""
    client, _ = box_client
    response = client.get("/api/boxes/missing-box")
    assert response.status_code == 404
    assert response.json() == {"detail": "Box not found"}
