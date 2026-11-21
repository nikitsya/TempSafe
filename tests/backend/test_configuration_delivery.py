"""Check retained configuration delivery, retries and the database commit boundary."""

import asyncio
import json
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from tempsafe.api.configuration import set_configuration
from tempsafe.db.models import Box, BoxConfiguration, ThresholdProfile
from tempsafe.monitoring.configuration import ConfigurationPublisher
from tempsafe.schemas import ThresholdSettingsCreate

pytestmark = pytest.mark.anyio


@pytest.fixture
def profile():
    return ThresholdProfile(
        profile_id=str(uuid4()), box_id="TS-01", lower_c=Decimal("0"),
        warning_c=Decimal("24"), upper_c=Decimal("25"), source_note="Bench test",
        is_demo=True, created_at=datetime(2026, 11, 21),
    )


@pytest.fixture
def delivery(profile):
    mqtt = Mock()
    mqtt.client.is_connected = True
    mqtt.on_connect.return_value = lambda handler: setattr(mqtt, "connected", handler)
    db = AsyncMock()
    db.begin = MagicMock()
    db.scalar.side_effect = [Box(box_id="TS-01"), profile]
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = db
    publisher = ConfigurationPublisher(mqtt, "TS-01", factory, interval=0.01)
    return publisher, mqtt, db, factory


async def test_publishes_device_contract_before_releasing_box_lock(delivery, profile):
    publisher, mqtt, db, factory = delivery

    def capture(topic, payload, **options):
        db.begin.return_value.__aexit__.assert_not_awaited()
        assert topic == "tempsafe/boxes/TS-01/configuration"
        assert options == {"qos": 1, "retain": True}
        assert json.loads(payload) == {
            "schema_version": 1, "box_id": "TS-01", "profile_id": profile.profile_id,
            "lower_c": "0.00", "warning_c": "24.00", "upper_c": "25.00",
        }

    mqtt.client.publish.side_effect = capture
    await publisher.publish_current()
    mqtt.client.publish.assert_called_once()
    db.begin.return_value.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("missing", ["box", "profile"])
async def test_missing_configuration_does_not_publish_defaults(delivery, missing):
    publisher, mqtt, db, factory = delivery
    db.scalar.side_effect = [None] if missing == "box" else [Box(box_id="TS-01"), None]
    await publisher.publish_current()
    mqtt.client.publish.assert_not_called()


async def test_disconnected_client_does_not_open_database(delivery):
    publisher, mqtt, db, factory = delivery
    mqtt.client.is_connected = False
    await publisher.publish_current()
    factory.assert_not_called()
    mqtt.client.publish.assert_not_called()


async def test_disconnect_during_database_read_does_not_publish(delivery, profile):
    publisher, mqtt, db, factory = delivery

    async def read(query):
        mqtt.client.is_connected = False
        return profile

    db.scalar.side_effect = read
    await publisher.publish_current()
    mqtt.client.publish.assert_not_called()


async def wait_for_worker(publisher, event):
    task = asyncio.create_task(publisher.run())
    try:
        await asyncio.wait_for(event.wait(), timeout=2)
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


@pytest.mark.parametrize("failure", [SQLAlchemyError("offline"), ConnectionError("offline"), TimeoutError()])
async def test_worker_recovers_without_another_api_request(delivery, failure):
    publisher, mqtt, db, factory = delivery
    recovered = asyncio.Event()
    attempts = 0

    async def publish():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise failure
        recovered.set()

    publisher.publish_current = publish
    await wait_for_worker(publisher, recovered)
    assert attempts == 2


async def test_worker_republishes_unchanged_profile_to_restore_retained_state(delivery, profile):
    publisher, mqtt, db, factory = delivery
    db.scalar.side_effect = [Box(box_id="TS-01"), profile] * 2
    repeated = asyncio.Event()
    mqtt.client.publish.side_effect = lambda *a, **kw: (
        repeated.set() if mqtt.client.publish.call_count == 2 else None
    )
    await wait_for_worker(publisher, repeated)
    assert mqtt.client.publish.call_args_list[0] == mqtt.client.publish.call_args_list[1]


async def test_retry_reads_new_selected_profile_instead_of_failed_payload(delivery, profile):
    publisher, mqtt, db, factory = delivery
    replacement = ThresholdProfile(
        profile_id=str(uuid4()), box_id="TS-01", lower_c=Decimal("1"),
        warning_c=Decimal("21"), upper_c=Decimal("22"),
    )
    db.scalar.side_effect = [Box(box_id="TS-01"), profile, Box(box_id="TS-01"), replacement]
    recovered = asyncio.Event()

    def publish(*args, **kwargs):
        if mqtt.client.publish.call_count == 1:
            raise ConnectionError("offline")
        recovered.set()

    mqtt.client.publish.side_effect = publish
    await wait_for_worker(publisher, recovered)
    assert json.loads(mqtt.client.publish.call_args.args[1])["profile_id"] == replacement.profile_id


async def test_update_received_during_publication_wakes_worker(delivery):
    publisher, mqtt, db, factory = delivery
    publisher.interval = 60
    repeated = asyncio.Event()
    attempts = 0

    async def publish():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            publisher.request_publish("TS-01")
        else:
            repeated.set()

    publisher.publish_current = publish
    await wait_for_worker(publisher, repeated)
    assert attempts == 2


async def test_reconnection_wakes_worker_for_current_configuration(delivery):
    publisher, mqtt, db, factory = delivery
    publisher.interval = 60
    reconnected = asyncio.Event()
    attempts = 0

    async def publish():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            asyncio.get_running_loop().call_soon(mqtt.connected, mqtt.client, {}, 0, {})
        else:
            reconnected.set()

    publisher.publish_current = publish
    await wait_for_worker(publisher, reconnected)
    assert attempts == 2


def test_other_box_and_failed_connection_do_not_request_publication(delivery):
    publisher, mqtt, db, factory = delivery
    publisher.request_publish("TS-02")
    mqtt.connected(mqtt.client, {}, 128, {})
    assert not publisher._requested.is_set()


def test_wildcard_configuration_topic_is_rejected():
    with pytest.raises(ValueError):
        ConfigurationPublisher(Mock(), "+", Mock())


@pytest.mark.parametrize("unchanged", [False, True])
@pytest.mark.parametrize("commit_fails", [False, True])
async def test_api_requests_delivery_only_after_commit(profile, unchanged, commit_fails):
    settings = ThresholdSettingsCreate(
        lower_c="0", warning_c="24", upper_c="25", source_note="Bench test"
    )
    db = AsyncMock()
    db.add = Mock()
    db.scalar.return_value = Box(box_id="TS-01")
    db.get.side_effect = [BoxConfiguration(box_id="TS-01", profile_id=profile.profile_id), profile]
    if not unchanged:
        profile.upper_c = Decimal("26")

    async def refresh(new_profile):
        new_profile.created_at = datetime(2026, 11, 21)

    db.refresh.side_effect = refresh
    publisher = Mock()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(configuration_publisher=publisher)))
    committed = False

    async def commit():
        nonlocal committed
        publisher.request_publish.assert_not_called()
        if commit_fails:
            raise SQLAlchemyError("commit failed")
        committed = True

    def wake(box_id):
        assert committed
        assert box_id == "TS-01"

    db.commit.side_effect = commit
    publisher.request_publish.side_effect = wake
    if commit_fails:
        with pytest.raises(SQLAlchemyError):
            await set_configuration("TS-01", settings, db, request)
        publisher.request_publish.assert_not_called()
        db.rollback.assert_awaited_once()
    else:
        result = await set_configuration("TS-01", settings, db, request)
        publisher.request_publish.assert_called_once_with("TS-01")
        assert result.upper_c == Decimal("25")
