"""Exercise Web Push subscription ownership, ingestion and delivery on MySQL."""

import base64
import secrets
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import text

from tempsafe import main
from tempsafe.api.auth import hasher
from tempsafe.db.models import AppUser, Box, BoxAccess, ThresholdProfile
from tempsafe.monitoring.push import deliver_one
from tempsafe.monitoring.readings import save_reading
from tempsafe.schemas import ReadingCreate
from tempsafe.settings import WebPushSettings

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def push_worker(monkeypatch, request):
    for key in ("PRIVATE_KEY", "PUBLIC_KEY", "SUBJECT"):
        monkeypatch.setenv("WEB_PUSH_" + key, "test")
    monkeypatch.delenv("WEB_PUSH_HOSTS", raising=False)
    if missing := getattr(request, "param", None):
        monkeypatch.delenv("WEB_PUSH_" + missing)
    worker = AsyncMock()
    monkeypatch.setattr(main, "run_worker", worker)
    return worker


@pytest.fixture
async def setup_push(client, db):
    box, profile = str(uuid4()), str(uuid4())
    db.add(Box(box_id=box, name="Test"))
    password = secrets.token_hex()
    user = AppUser(auth_subject=str(uuid4()), password_hash=hasher.hash(password))
    other = AppUser(auth_subject=str(uuid4()), password_hash=user.password_hash)
    db.add_all([user, other])
    await db.flush()
    db.add_all([BoxAccess(user_id=user.user_id, box_id=box), ThresholdProfile(
        box_id=box, profile_id=profile, lower_c=0, warning_c=24, upper_c=25, source_note="Test")])
    await db.commit()
    point = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    body = {"endpoint": "https://fcm.googleapis.com/" + str(uuid4()), "keys": {
        "p256dh": base64.urlsafe_b64encode(point).decode().rstrip("="), "auth": secrets.token_urlsafe(16)}}

    async def login(account):
        assert (await client.post("/api/login", json={"username": account.auth_subject, "password": password})).status_code == 204

    async def reading(sequence, temperature, age=1, sensor="inside"):
        payload = ReadingCreate(sample_id=uuid4(), box_id=box, profile_id=profile, sequence_no=sequence,
                                clock_reliable=True, observed_at=datetime.now(UTC) - timedelta(seconds=age),
                                temperature_c=temperature, sensor_location=sensor, quality="valid")
        await save_reading(db, payload)

    return login, user, other, body, reading


@pytest.mark.parametrize(("path", "method", "field"), [
    ("/api/push/public-key", "get", "applicationServerKey"),
    ("/api/push/subscriptions", "post", "id"),
])
async def test_push_response_schema(client, path, method, field):
    spec = (await client.get("/openapi.json")).json()
    response = spec["paths"][path][method]["responses"]["200"]
    schema_ref = response["content"]["application/json"]["schema"]["$ref"]
    schema = spec["components"]["schemas"][schema_ref.rsplit("/", 1)[-1]]
    assert schema["required"] == [field]
    assert schema["properties"][field]["type"] == "string"


async def test_manage_subscriptions(setup_push, client, db, push_worker):
    login, user, other, body, _ = setup_push
    path = "/api/push/subscriptions"
    assert (await client.post(path, json=body)).status_code == 401
    await login(user)
    assert (await client.get("/api/push/public-key")).json() == {"applicationServerKey": "test"}
    push_worker.assert_awaited_once_with(main.app.state.web_push_settings)
    assert (await client.post(path, json=body | {"endpoint": "https://other.example/id"})).status_code == 422
    result = await client.post(path, json=body)
    assert result.status_code == 200
    sub = result.json()["id"]
    assert (await client.post(path, json=body)).json()["id"] == sub
    await login(other)
    assert (await client.post(path, json=body)).status_code == 409
    assert (await client.delete(f"{path}/{sub}")).status_code == 204
    assert await db.scalar(text("SELECT COUNT(*) FROM push_subscriptions WHERE endpoint_id=:id"), {"id": sub}) == 1
    await login(user)
    assert (await client.delete(f"{path}/{sub}")).status_code == 204
    assert await db.scalar(text("SELECT COUNT(*) FROM push_subscriptions WHERE endpoint_id=:id"), {"id": sub}) == 0


@pytest.mark.parametrize("push_worker", ["PUBLIC_KEY", "PRIVATE_KEY", "SUBJECT"], indirect=True)
async def test_incomplete_push_configuration(setup_push, client, push_worker):
    login, user, _, body, _ = setup_push
    await login(user)
    assert (await client.get("/api/push/public-key")).status_code == 503
    assert (await client.post("/api/push/subscriptions", json=body)).status_code == 503
    push_worker.assert_not_called()


async def test_transition_selection_and_delivery(setup_push, client, db):
    login, user, other, body, reading = setup_push
    for account in (user, other):
        await login(account)
        assert (await client.post("/api/push/subscriptions", json=body | {
            "endpoint": body["endpoint"] + str(account.user_id)})).status_code == 200
    await reading(1, 23)
    await reading(2, 24)
    await reading(3, 24)
    await reading(4, 29)
    await reading(5, 20, age=300)
    await reading(6, 23, sensor="outside")
    await reading(7, 23, age=10)
    calls = []

    def accepted(job, ttl):
        calls.append((job.state, job.user_id, ttl))
        return 201

    hosts = main.app.state.web_push_settings.allowed_hosts
    while await deliver_one(db, accepted, hosts):
        pass
    assert len(calls) == 1
    assert calls[0][:2] == ("Alert", user.user_id)
    statuses = (await db.execute(text("SELECT status FROM push_deliveries ORDER BY id"))).scalars().all()
    assert statuses == ["cancelled", "accepted"]
    await reading(8, 22)
    await reading(9, 26)
    await db.execute(text("DELETE FROM box_access WHERE user_id=:id"), {"id": user.user_id})
    assert await deliver_one(db, accepted, hosts)
    assert len(calls) == 1


async def test_delivery_retry_and_expired_subscription(setup_push, client, db):
    login, user, _, body, reading = setup_push
    await login(user)
    sub = (await client.post("/api/push/subscriptions", json=body)).json()["id"]
    await reading(1, 30)
    hosts = main.app.state.web_push_settings.allowed_hosts
    assert await deliver_one(db, lambda job, ttl: 503, hosts)
    status = text("SELECT status,attempts,http_status FROM push_deliveries WHERE endpoint_id=:id")
    assert (await db.execute(status, {"id": sub})).one() == ("pending", 1, 503)
    await db.execute(text("UPDATE push_deliveries SET next_attempt=UTC_TIMESTAMP() WHERE endpoint_id=:id"), {"id": sub})
    assert await deliver_one(db, lambda job, ttl: 410, hosts)
    assert (await db.execute(status, {"id": sub})).one() == ("failed", 2, 410)
    assert not await db.scalar(text("SELECT enabled FROM push_subscriptions WHERE endpoint_id=:id"), {"id": sub})


def test_provider_request_is_encrypted_and_signed(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    import http_ece
    from requests import Response
    from tempsafe.monitoring.push import PushSession, send

    key = ec.generate_private_key(ec.SECP256R1())
    pem = tmp_path / "vapid.pem"
    pem.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                      serialization.NoEncryption()))
    monkeypatch.setenv("WEB_PUSH_PRIVATE_KEY", str(pem))
    monkeypatch.setenv("WEB_PUSH_SUBJECT", "mailto:operator@example.test")
    browser = ec.generate_private_key(ec.SECP256R1())
    point = browser.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    auth = secrets.token_bytes(16)
    endpoint = "https://fcm.googleapis.com/example"
    job = SimpleNamespace(endpoint=endpoint, p256dh=base64.urlsafe_b64encode(point).decode().rstrip("="),
                          auth_secret=base64.urlsafe_b64encode(auth).decode().rstrip("="), state="Warning",
                          box_id="TS-01", sample_id=str(uuid4()), temperature_c=24, observed_at=datetime.now(UTC).replace(tzinfo=None))

    def capture(self, request, **options):
        assert request.url == endpoint and not options["allow_redirects"]
        assert request.headers["Authorization"].startswith("vapid ")
        assert request.headers["TTL"] == "30"
        payload = json.loads(http_ece.decrypt(request.body, private_key=browser, auth_secret=auth, version="aes128gcm"))
        assert payload["sample_id"] == job.sample_id and payload["state"] == "Warning"
        response = Response()
        response.status_code = 201
        response._content = b""
        return response

    monkeypatch.setattr(PushSession, "send", capture)
    assert send(job, 30, WebPushSettings.from_env()) == 201
