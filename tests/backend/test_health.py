"""Smoke tests for the backend API and its generated documentation."""

from fastapi.testclient import TestClient

from temsafe.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_includes_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "TEMSAFE API"
    assert "get" in schema["paths"]["/api/health"]
