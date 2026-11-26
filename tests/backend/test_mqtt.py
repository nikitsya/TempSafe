"""Check topic authorisation and the boundary between storage and acknowledgement."""

import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from tempsafe.mqtt import ReadingConsumer

pytestmark = pytest.mark.anyio


@pytest.fixture
def consumer_data():
    factory = MagicMock()
    save = AsyncMock()
    consumer = ReadingConsumer("TS-01", factory, save)
    client = Mock()
    payload = dict(
        schema_version=1, sample_id=str(uuid4()), box_id="TS-01",
        sequence_no=12, profile_id=str(uuid4()), observed_at="2026-11-03T12:00:00Z",
        clock_reliable=True, temperature_c="23.45", quality="valid",
    )
    message = SimpleNamespace(topic=consumer.readings_topic, retain=False,
                              payload=json.dumps(payload).encode())
    return consumer, factory, save, client, payload, message


@pytest.mark.parametrize("location", [None, "inside", "outside"])
async def test_acknowledgement_follows_successful_storage(consumer_data, location):
    consumer, factory, save, client, payload, message = consumer_data
    if location is not None:
        payload["sensor_location"] = location
        message.payload = json.dumps(payload).encode()
    save.side_effect = lambda *args: client.publish.assert_not_called()
    ack = await consumer.store(message.topic, message.payload, message.retain)
    save.assert_awaited_once()
    assert str(save.call_args.args[1].sample_id) == payload["sample_id"]
    assert save.call_args.args[1].sensor_location == (location or "inside")
    assert json.loads(ack) == dict(schema_version=1, sample_id=payload["sample_id"], status="stored")


@pytest.mark.parametrize("failure", [ValueError("conflict"), SQLAlchemyError("offline")])
async def test_failed_storage_never_acknowledges(consumer_data, failure):
    consumer, factory, save, client, payload, message = consumer_data
    save.side_effect = failure
    ack = await consumer.store(message.topic, message.payload, message.retain)
    assert ack is None


@pytest.mark.parametrize("case", ["topic", "box", "retained", "invalid", "large", "quality"])
async def test_rejects_unauthorised_or_invalid_readings(consumer_data, case):
    consumer, factory, save, client, payload, message = consumer_data
    if case == "topic":
        message.topic = "tempsafe/boxes/TS-02/readings"
    elif case == "box":
        payload["box_id"] = "TS-02"
        message.payload = json.dumps(payload).encode()
    elif case == "retained":
        message.retain = True
    elif case == "invalid":
        message.payload = b"not-json"
    elif case == "large":
        message.payload = b" " * 4097
    elif case == "quality":
        payload["quality"] = "sensor_error"
        message.payload = json.dumps(payload).encode()
    ack = await consumer.store(message.topic, message.payload, message.retain)
    factory.assert_not_called()
    save.assert_not_called()
    assert ack is None


async def test_repeated_reading_is_passed_unchanged_to_idempotent_storage(consumer_data):
    consumer, factory, save, client, payload, message = consumer_data
    ack = await consumer.store(message.topic, message.payload, message.retain)
    ack = await consumer.store(message.topic, message.payload, message.retain)
    assert save.call_args_list[0].args[1] == save.call_args_list[1].args[1]
    assert json.loads(ack)["sample_id"] == payload["sample_id"]


def test_wildcard_box_configuration_is_rejected():
    with pytest.raises(ValueError):
        ReadingConsumer("+", Mock(), Mock())


@pytest.mark.parametrize("unreliable", [False, True])
async def test_sensor_errors_and_unknown_times_are_preserved(consumer_data, unreliable):
    consumer, factory, save, client, payload, message = consumer_data
    payload.update(quality="sensor_error", temperature_c=None)
    if unreliable:
        payload.update(clock_reliable=False, observed_at=None)
    message.payload = json.dumps(payload).encode()
    ack = await consumer.store(message.topic, message.payload, message.retain)
    reading = save.call_args.args[1]
    assert reading.temperature_c is None
    assert reading.clock_reliable is not unreliable
    assert (reading.observed_at is None) is unreliable
    assert ack is not None


def test_fastmqtt_dispatch_and_reconnection(monkeypatch):
    import asyncio
    import ssl
    from tempsafe.mqtt import create_mqtt

    monkeypatch.setenv("MQTT_ENABLED", "true")
    monkeypatch.setenv("MQTT_HOST", "mqtt.example.test")
    monkeypatch.setenv("MQTT_PASSWORD", "test-password")
    monkeypatch.setenv("MQTT_BOX_ID", "TS-01")
    store = AsyncMock(return_value='{"status":"stored"}')
    monkeypatch.setattr(ReadingConsumer, "store", store)

    async def scenario():
        mqtt = create_mqtt()
        assert mqtt.config.ssl.verify_mode == ssl.CERT_REQUIRED
        assert mqtt.config.ssl.check_hostname
        assert mqtt.config.reconnect_retries == -1
        mqtt.client.subscribe = Mock()
        for _ in range(2):
            mqtt.client.on_connect(0, 0, {})
        assert mqtt.client.subscribe.call_count == 4
        first, applied, again, applied_again = [call.args[0] for call in mqtt.client.subscribe.call_args_list]
        assert first.topic == again.topic
        assert applied.topic == applied_again.topic == "tempsafe/boxes/TS-01/configuration/applied"
        subscription = first
        assert subscription.topic == "tempsafe/boxes/TS-01/readings"
        assert subscription.retain_as_published
        client = mqtt.client
        client._connack_received.set()
        client._connection = Mock()
        client._connection.is_closing.return_value = False
        client.publish = Mock()
        client.publish.side_effect = lambda *a, **k: store.assert_awaited_once()
        await mqtt.client.on_message(subscription.topic, b"payload", 1, {"retain": 1})
        store.assert_awaited_once_with(subscription.topic, b"payload", True)
        client.publish.assert_called_once_with("tempsafe/boxes/TS-01/acks", '{"status":"stored"}', qos=1, retain=False)
        store.return_value = None
        client.publish.reset_mock()
        await mqtt.client.on_message(subscription.topic, b"bad", 1, {})
        client.publish.assert_not_called()

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", [None, "startup", "shutdown"])
async def test_lifespan_stops_mqtt_before_closing_database_pool(monkeypatch, failure):
    from tempsafe import main

    mqtt = Mock(mqtt_startup=AsyncMock(), mqtt_shutdown=AsyncMock())
    if failure == "startup":
        mqtt.mqtt_startup.side_effect = ConnectionError(failure)
    elif failure == "shutdown":
        mqtt.mqtt_shutdown.side_effect = ConnectionError(failure)
    dispose = AsyncMock(side_effect=mqtt.mqtt_shutdown.assert_awaited_once)
    monkeypatch.setattr(main, "create_mqtt", lambda: mqtt)
    monkeypatch.setattr(main, "engine", Mock(dispose=dispose))

    with pytest.raises(ConnectionError, match=failure) if failure else nullcontext():
        async with main.app.router.lifespan_context(main.app):
            mqtt.mqtt_startup.assert_awaited_once()
            mqtt.mqtt_shutdown.assert_not_awaited()
            dispose.assert_not_awaited()

    dispose.assert_awaited_once()


async def test_lifespan_cancels_configuration_worker_before_mqtt_shutdown(monkeypatch):
    import asyncio
    from tempsafe import main

    started = asyncio.Event()
    stopped = asyncio.Event()

    async def run():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    publisher = Mock(run=run)
    mqtt = Mock(mqtt_startup=AsyncMock(), mqtt_shutdown=AsyncMock())

    async def disconnect():
        assert stopped.is_set()
        assert main.app.state.configuration_publisher is None

    mqtt.mqtt_shutdown.side_effect = disconnect
    dispose = AsyncMock(side_effect=mqtt.mqtt_shutdown.assert_awaited_once)
    monkeypatch.setattr(main, "create_mqtt", lambda: mqtt)
    monkeypatch.setattr(main, "ConfigurationPublisher", lambda *args: publisher)
    monkeypatch.setattr(main, "engine", Mock(dispose=dispose))

    async with main.app.router.lifespan_context(main.app):
        await asyncio.wait_for(started.wait(), timeout=1)
        assert main.app.state.configuration_publisher is publisher

    dispose.assert_awaited_once()


def test_mqtt_disabled_or_missing_configuration(monkeypatch):
    from tempsafe.mqtt import create_mqtt
    monkeypatch.setenv("MQTT_ENABLED", "false")
    assert create_mqtt() is None
    monkeypatch.setenv("MQTT_ENABLED", "true")
    monkeypatch.delenv("MQTT_PASSWORD", raising=False)
    monkeypatch.setenv("MQTT_HOST", "mqtt.example.test")
    with pytest.raises(ValueError, match="MQTT_PASSWORD"):
        create_mqtt()
