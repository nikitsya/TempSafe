"""Check box responses using a substituted database session."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from tempsafe.db.models import Box
from tempsafe.db.session import get_db
from tempsafe.main import app


@pytest.fixture
def box_client(grant_boxes):
    """Provide a test client without querying the real database."""
    grant_boxes("test-box")
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


def test_get_box_returns_details(box_client):
    """Return the box identifier and name in the expected JSON format."""
    client, db = box_client
    db.execute.return_value.scalars.return_value.first.return_value = Box(
        box_id="test-box", name="Test box"
    )
    response = client.get("/api/boxes/test-box")
    assert response.status_code == 200
    assert response.json() == {
        "box_id": "test-box",
        "name": "Test box",
    }


def test_get_box_returns_404(box_client):
    """Report a missing box without returning an empty success response."""
    client, _ = box_client
    response = client.get("/api/boxes/missing-box")
    assert response.status_code == 404
    assert response.json() == {"detail": "Box not found"}
