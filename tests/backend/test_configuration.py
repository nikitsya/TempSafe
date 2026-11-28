"""Check assigned box configuration and historical integrity against isolated MySQL."""

import json
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from tempsafe.db.models import Box, BoxConfiguration, TemperatureSample, ThresholdProfile
from tempsafe.monitoring.configuration import ConfigurationPublisher

pytestmark = pytest.mark.anyio

SETTINGS = {"lower_c": "0.00", "warning_c": "24.00", "upper_c": "25.00", "source_note": "Synthetic test profile"}


@pytest.fixture
async def configured_api(grant_boxes, client, db):
    box_id = f"pytest-{uuid4()}"
    grant_boxes(box_id)
    db.add(Box(box_id=box_id, name="Configuration test"))
    await db.commit()
    return client, db, box_id


@pytest.mark.parametrize("changes", [
    {"lower_c": "24"}, {"warning_c": "25"}, {"upper_c": "23"},
    {"upper_c": "81"}, {"lower_c": "-41"}, {"warning_c": "24.001"},
    {"lower_c": "NaN"}, {"upper_c": "Infinity"}, {"source_note": "   "},
    {"unexpected": True},
])
async def test_invalid_limits_do_not_write(configured_api, changes):
    client, db, box_id = configured_api
    result = await client.put(f"/api/boxes/{box_id}/configuration", json=SETTINGS | changes)
    assert result.status_code == 422
    assert await db.get(BoxConfiguration, box_id) is None
    assert await db.scalar(
        select(func.count()).select_from(ThresholdProfile).where(ThresholdProfile.box_id == box_id)) == 0


async def test_missing_box_and_unconfigured_box(configured_api):
    client, db, box_id = configured_api
    assert (await client.get(f"/api/boxes/{box_id}/configuration")).status_code == 404
    assert (await client.put("/api/boxes/missing/configuration", json=SETTINGS)).status_code == 404


async def test_change_preserves_history_and_identical_retry(configured_api):
    client, db, box_id = configured_api
    path = f"/api/boxes/{box_id}/configuration"
    first = await client.put(path, json=SETTINGS)
    assert first.status_code == 200
    original = first.json()
    assert original["is_demo"] is True
    assert (await client.put(path, json=SETTINGS)).json()["profile_id"] == original["profile_id"]
    sample_id = str(uuid4())
    db.add(TemperatureSample(
        sample_id=sample_id, box_id=box_id, profile_id=original["profile_id"],
        sequence_no=1, observed_at=datetime(2026, 1, 1), clock_reliable=True,
        temperature_c=Decimal("24.50"), quality="valid",
    ))
    await db.commit()
    changed = await client.put(path, json=SETTINGS | {"warning_c": "20", "upper_c": "23"})
    assert changed.status_code == 200
    assert changed.json()["profile_id"] != original["profile_id"]
    assert (await client.get(path)).json()["profile_id"] == changed.json()["profile_id"]
    history = (await client.get(f"/api/boxes/{box_id}/readings/latest")).json()
    assert history["profile_id"] == original["profile_id"]
    assert history["temperature_state"] == "Warning"
    assert (await db.get(ThresholdProfile, original["profile_id"])).upper_c == Decimal("25")
    assert await db.scalar(
        select(func.count()).select_from(ThresholdProfile).where(ThresholdProfile.box_id == box_id)) == 2


async def test_publisher_reads_the_selected_profile_from_mysql(configured_api):
    client, db, box_id = configured_api
    mqtt = Mock()
    mqtt.client.is_connected = True
    factory = async_sessionmaker(
        bind=await db.connection(), join_transaction_mode="create_savepoint", expire_on_commit=False,
    )
    publisher = ConfigurationPublisher(mqtt, box_id, factory)
    await publisher.publish_current()
    mqtt.client.publish.assert_not_called()

    for upper in ("25.00", "26.00"):
        response = await client.put(f"/api/boxes/{box_id}/configuration", json=SETTINGS | {"upper_c": upper})
        assert response.status_code == 200
        await publisher.publish_current()
        call = mqtt.client.publish.call_args
        assert call.args[0] == f"tempsafe/boxes/{box_id}/configuration"
        assert call.kwargs == {"qos": 1, "retain": True}
        assert json.loads(call.args[1]) == {
            "schema_version": 1, "box_id": box_id, "profile_id": response.json()["profile_id"],
            "lower_c": "0.00", "warning_c": "24.00", "upper_c": upper,
        }


async def test_only_current_device_confirmation_changes_applied_profile(configured_api, monkeypatch):
    from tempsafe import mqtt

    client, db, box_id = configured_api
    monkeypatch.setenv("MQTT_BOX_ID", box_id)
    monkeypatch.setenv("MQTT_ENABLED", "true")
    monkeypatch.setenv("TEMPSAFE_LOCAL_MQTT", "1")
    monkeypatch.setattr("tempsafe.mqtt.AsyncSessionLocal", async_sessionmaker(
        bind=await db.connection(), join_transaction_mode="create_savepoint",
    ))
    broker = mqtt.create_mqtt()
    assert broker is not None
    topic = f"tempsafe/boxes/{box_id}/configuration/applied"
    path = f"/api/boxes/{box_id}/configuration"
    first = (await client.put(path, json=SETTINGS)).json()["profile_id"]

    async def report(profile_id, retained=False, **changes):
        payload = {"schema_version": 1, "box_id": box_id, "profile_id": profile_id} | changes
        await broker.client.on_message(topic, json.dumps(payload).encode(), 1, {"retain": retained})
        return await db.scalar(select(BoxConfiguration.applied_profile_id).where(BoxConfiguration.box_id == box_id))

    assert await report(first, retained=True) is None
    assert await report(first, box_id="other-box") is None
    assert await report(first, schema_version=True) is None
    assert await report(first) == first
    second = (await client.put(path, json=SETTINGS | {"upper_c": "26"})).json()["profile_id"]
    assert await report(first) == first
    assert await report(second) == second
    assert await report(first) == second
