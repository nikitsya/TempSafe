"""Check operator configuration and historical integrity against isolated MySQL."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tempsafe.db.models import Box, BoxConfiguration, TemperatureSample, ThresholdProfile
from tempsafe.db.session import engine, get_db
from tempsafe.main import app

TOKEN = "test-configuration-token-32-characters-long"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
SETTINGS = {"lower_c": "0.00", "warning_c": "24.00", "upper_c": "25.00", "source_note": "Synthetic test profile"}


@pytest.fixture
def configured_api(monkeypatch, grant_boxes):
    monkeypatch.setenv("TEMPSAFE_CONFIG_ADMIN_TOKEN", TOKEN)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            box_id = f"pytest-{uuid4()}"
            grant_boxes(box_id)
            db.add(Box(box_id=box_id, name="Configuration test"))
            db.commit()

            def override():
                yield db

            app.dependency_overrides[get_db] = override
            try:
                with TestClient(app) as client:
                    yield client, db, box_id
            finally:
                app.dependency_overrides.pop(get_db, None)
        transaction.rollback()


def test_configuration_requires_operator_key(monkeypatch, grant_boxes):
    grant_boxes("TS-01")
    with TestClient(app) as client:
        monkeypatch.delenv("TEMPSAFE_CONFIG_ADMIN_TOKEN", raising=False)
        assert client.get("/api/boxes/TS-01/configuration").status_code == 503
        monkeypatch.setenv("TEMPSAFE_CONFIG_ADMIN_TOKEN", TOKEN)
        for headers in [{}, {"Authorization": "Bearer incorrect"}]:
            assert client.put("/api/boxes/TS-01/configuration", json=SETTINGS, headers=headers).status_code == 401


@pytest.mark.parametrize("changes", [
    {"lower_c": "24"}, {"warning_c": "25"}, {"upper_c": "23"},
    {"upper_c": "81"}, {"lower_c": "-41"}, {"warning_c": "24.001"},
    {"lower_c": "NaN"}, {"upper_c": "Infinity"}, {"source_note": "   "},
    {"unexpected": True},
])
def test_invalid_limits_do_not_write(configured_api, changes):
    client, db, box_id = configured_api
    result = client.put(f"/api/boxes/{box_id}/configuration", json=SETTINGS | changes, headers=HEADERS)
    assert result.status_code == 422
    assert db.get(BoxConfiguration, box_id) is None
    assert db.scalar(select(func.count()).select_from(ThresholdProfile).where(ThresholdProfile.box_id == box_id)) == 0


def test_missing_box_and_unconfigured_box(configured_api):
    client, db, box_id = configured_api
    assert client.get(f"/api/boxes/{box_id}/configuration", headers=HEADERS).status_code == 404
    assert client.put("/api/boxes/missing/configuration", json=SETTINGS, headers=HEADERS).status_code == 404


def test_change_preserves_history_and_identical_retry(configured_api):
    client, db, box_id = configured_api
    path = f"/api/boxes/{box_id}/configuration"
    first = client.put(path, json=SETTINGS, headers=HEADERS)
    assert first.status_code == 200
    original = first.json()
    assert original["is_demo"] is True
    assert client.put(path, json=SETTINGS, headers=HEADERS).json()["profile_id"] == original["profile_id"]
    sample_id = str(uuid4())
    db.add(TemperatureSample(
        sample_id=sample_id, box_id=box_id, profile_id=original["profile_id"],
        sequence_no=1, observed_at=datetime(2026, 1, 1), clock_reliable=True,
        temperature_c=Decimal("24.50"), quality="valid",
    ))
    db.commit()
    changed = client.put(path, json=SETTINGS | {"warning_c": "20", "upper_c": "23"}, headers=HEADERS)
    assert changed.status_code == 200
    assert changed.json()["profile_id"] != original["profile_id"]
    assert client.get(path, headers=HEADERS).json()["profile_id"] == changed.json()["profile_id"]
    history = client.get(f"/api/boxes/{box_id}/readings/latest").json()
    assert history["profile_id"] == original["profile_id"]
    assert history["temperature_state"] == "Warning"
    assert db.get(ThresholdProfile, original["profile_id"]).upper_c == Decimal("25")
    assert db.scalar(select(func.count()).select_from(ThresholdProfile).where(ThresholdProfile.box_id == box_id)) == 2
