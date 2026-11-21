"""Exercise authentication through HTTPS requests and a transactional MySQL session."""

import secrets
from datetime import timedelta
from uuid import uuid4

import pytest

from tempsafe.api.auth import COOKIE, hasher, token_digest, utc_now
from tempsafe.db.models import AppUser, Box, BoxAccess, TemperatureSample, ThresholdProfile, UserSession

pytestmark = pytest.mark.anyio


@pytest.fixture
async def account(client, db):
    username = str(uuid4())
    password = secrets.token_urlsafe()
    box_id = str(uuid4())
    user = AppUser(auth_subject=username, password_hash=hasher.hash(password))
    db.add_all([user, Box(box_id=box_id, name="Assigned box")])
    await db.flush()
    db.add(BoxAccess(user_id=user.user_id, box_id=box_id))
    await db.commit()
    return client, {"username": username, "password": password}, box_id, db


@pytest.mark.parametrize("path", [
    "/api/me", "/api/boxes/TS-01", "/api/boxes/TS-01/configuration", "/api/boxes/TS-01/readings",
    "/api/boxes/TS-01/status", "/api/boxes/TS-01/readings/latest", "/api/readings", "/api/readings/example",
])
async def test_anonymous_read_is_rejected(path, client):
    assert (await client.get(path)).status_code == 401


async def test_login_scope_and_logout(account):
    client, credentials, box_id, db = account
    assert (await client.post("/api/login", json=credentials | {"password": "wrong"})).status_code == 401
    assert COOKIE not in client.cookies
    response = await client.post("/api/login", json=credentials)
    assert response.status_code == 204
    for flag in ["HttpOnly", "Secure", "SameSite=strict", "Path=/"]:
        assert flag in response.headers["set-cookie"]
    token = client.cookies[COOKIE]
    assert await db.get(UserSession, token_digest(token))
    assert (await client.get(f"/api/boxes/{box_id}")).status_code == 200
    other_box = str(uuid4())
    db.add(Box(box_id=other_box, name="Another user's box"))
    await db.commit()
    assert (await client.get("/api/me")).json() == {"username": credentials["username"], "box_ids": [box_id]}
    assert (await client.get(
        f"/api/boxes/{other_box}/readings?start_date=2026-11-01&end_date=2026-11-01")).status_code == 404
    assert (await client.get(f"/api/boxes/{other_box}/status")).status_code == 404
    assert (await client.get(f"/api/boxes/{other_box}")).status_code == 404
    assert (await client.get("/api/readings")).json() == []
    assert (await client.post("/api/readings", json={})).status_code == 401
    assert (await client.post("/api/logout")).status_code == 204
    assert COOKIE not in client.cookies
    assert (await client.get("/api/readings", headers={"Cookie": f"{COOKIE}={token}"})).status_code == 401


async def test_session_can_change_only_assigned_box_limits(account):
    client, credentials, box_id, db = account
    limits = {"lower_c": "0", "warning_c": "24", "upper_c": "25", "source_note": "Test"}
    url = f"/api/boxes/{box_id}/configuration"
    assert (await client.put(url, json=limits)).status_code == 401
    await client.post("/api/login", json=credentials)
    other_id = str(uuid4())
    db.add(Box(box_id=other_id, name="Unassigned box"))
    await db.commit()
    other = f"/api/boxes/{other_id}/configuration"
    assert (await client.get(other)).status_code == 404
    assert (await client.put(other, json=limits)).status_code == 404
    assert (await client.put(url, json=limits)).status_code == 200
    assert (await client.get(url)).json()["warning_c"] == "24.00"


async def test_readings_are_limited_to_assigned_boxes(account):
    client, credentials, box_id, db = account
    other_id = str(uuid4())
    db.add(Box(box_id=other_id, name="Unassigned box"))
    await db.flush()
    sample_ids = []
    for box in (box_id, other_id):
        profile_id = str(uuid4())
        db.add(ThresholdProfile(profile_id=profile_id, box_id=box, lower_c=0, warning_c=24,
                                upper_c=25, source_note="Test", is_demo=True))
        await db.flush()
        sample_id = str(uuid4())
        db.add(TemperatureSample(sample_id=sample_id, box_id=box, sequence_no=1,
                                 profile_id=profile_id, clock_reliable=False, quality="sensor_error"))
        sample_ids.append(sample_id)
    await db.commit()
    assert (await client.post("/api/login", json=credentials)).status_code == 204
    readings = (await client.get("/api/readings")).json()
    assert [reading["sample_id"] for reading in readings] == sample_ids[:1]
    assert (await client.get(f"/api/readings/{sample_ids[0]}")).status_code == 200
    assert (await client.get(f"/api/readings/{sample_ids[1]}")).status_code == 404
    assert (await client.get(f"/api/boxes/{other_id}/readings/latest")).status_code == 404


async def test_expired_session(account):
    client, credentials, _, db = account
    await client.post("/api/login", json=credentials)
    session = await db.get(UserSession, token_digest(client.cookies[COOKIE]))
    session.expires_at = utc_now() - timedelta(seconds=1)
    await db.commit()
    assert (await client.get("/api/readings")).status_code == 401


async def test_device_key_is_separate_from_browser_access(monkeypatch, client):
    key = secrets.token_urlsafe(32)
    monkeypatch.setenv("TEMPSAFE_DEVICE_KEY", key)
    monkeypatch.setenv("TEMPSAFE_DEVICE_BOX_ID", "TS-01")
    for headers in [{}, {"X-Device-Key": "wrong"}]:
        assert (await client.post("/api/readings", headers=headers, json={})).status_code == 401
    assert (await client.get("/api/readings", headers={"X-Device-Key": key})).status_code == 401
    monkeypatch.delenv("TEMPSAFE_DEVICE_KEY")
    assert (await client.post("/api/readings", headers={"X-Device-Key": key}, json={})).status_code == 401
