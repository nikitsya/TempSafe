"""Exercise authentication through HTTPS requests and a transactional MySQL session."""

import secrets
from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from temsafe.api.auth import COOKIE, hasher, token_digest, utc_now
from temsafe.database import engine, get_db
from temsafe.main import app
from temsafe.models import AppUser, Box, BoxAccess, TemperatureSample, ThresholdProfile, UserSession


@pytest.fixture
def account(monkeypatch):
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            username = str(uuid4())
            password = secrets.token_urlsafe()
            box_id = str(uuid4())
            user = AppUser(auth_subject=username, password_hash=hasher.hash(password))
            db.add_all([user, Box(box_id=box_id, name="Assigned box")])
            db.flush()
            db.add(BoxAccess(user_id=user.user_id, box_id=box_id))
            db.commit()
            monkeypatch.setitem(app.dependency_overrides, get_db, lambda: db)
            with TestClient(app, base_url="https://testserver") as client:
                yield client, {"username": username, "password": password}, box_id, db
        transaction.rollback()


@pytest.mark.parametrize("path", [
    "/api/boxes/TS-01", "/api/boxes/TS-01/configuration", "/api/boxes/TS-01/readings",
    "/api/boxes/TS-01/readings/latest", "/api/readings", "/api/readings/example",
])
def test_anonymous_read_is_rejected(path):
    with TestClient(app) as client:
        assert client.get(path).status_code == 401


def test_login_scope_and_logout(account):
    client, credentials, box_id, db = account
    assert client.post("/api/login", json=credentials | {"password": "wrong"}).status_code == 401
    assert COOKIE not in client.cookies
    response = client.post("/api/login", json=credentials)
    assert response.status_code == 204
    for flag in ["HttpOnly", "Secure", "SameSite=strict", "Path=/"]:
        assert flag in response.headers["set-cookie"]
    token = client.cookies[COOKIE]
    assert db.get(UserSession, token_digest(token))
    assert client.get(f"/api/boxes/{box_id}").status_code == 200
    other_box = str(uuid4())
    db.add(Box(box_id=other_box, name="Another user's box"))
    db.commit()
    assert client.get(f"/api/boxes/{other_box}").status_code == 404
    assert client.get("/api/readings").json() == []
    assert client.post("/api/readings", json={}).status_code == 401
    assert client.post("/api/logout").status_code == 204
    assert COOKIE not in client.cookies
    assert client.get("/api/readings", headers={"Cookie": f"{COOKIE}={token}"}).status_code == 401


def test_readings_are_limited_to_assigned_boxes(account):
    client, credentials, box_id, db = account
    other_id = str(uuid4())
    db.add(Box(box_id=other_id, name="Unassigned box"))
    db.flush()
    sample_ids = []
    for box in (box_id, other_id):
        profile_id = str(uuid4())
        db.add(ThresholdProfile(profile_id=profile_id, box_id=box, lower_c=0, warning_c=24,
                                upper_c=25, source_note="Test", is_demo=True))
        db.flush()
        sample_id = str(uuid4())
        db.add(TemperatureSample(sample_id=sample_id, box_id=box, sequence_no=1,
                                 profile_id=profile_id, clock_reliable=False, quality="sensor_error"))
        sample_ids.append(sample_id)
    db.commit()
    assert client.post("/api/login", json=credentials).status_code == 204
    readings = client.get("/api/readings").json()
    assert [reading["sample_id"] for reading in readings] == sample_ids[:1]
    assert client.get(f"/api/readings/{sample_ids[0]}").status_code == 200
    assert client.get(f"/api/readings/{sample_ids[1]}").status_code == 404
    assert client.get(f"/api/boxes/{other_id}/readings/latest").status_code == 404


def test_expired_session(account):
    client, credentials, _, db = account
    client.post("/api/login", json=credentials)
    session = db.get(UserSession, token_digest(client.cookies[COOKIE]))
    session.expires_at = utc_now() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/readings").status_code == 401


def test_device_key_is_separate_from_browser_access(monkeypatch):
    key = secrets.token_urlsafe(32)
    monkeypatch.setenv("TEMSAFE_DEVICE_KEY", key)
    monkeypatch.setenv("TEMSAFE_DEVICE_BOX_ID", "TS-01")
    with TestClient(app) as client:
        for headers in [{}, {"X-Device-Key": "wrong"}]:
            assert client.post("/api/readings", headers=headers, json={}).status_code == 401
        assert client.get("/api/readings", headers={"X-Device-Key": key}).status_code == 401
        monkeypatch.delenv("TEMSAFE_DEVICE_KEY")
        assert client.post("/api/readings", headers={"X-Device-Key": key}, json={}).status_code == 401
