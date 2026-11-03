"""Check topic authorisation and the boundary between storage and acknowledgement."""

import json
import pytest
from sqlalchemy.exc import SQLAlchemyError
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock
from uuid import uuid4

from temsafe.mqtt_worker import ReadingConsumer


@pytest.fixture
def consumer_data():
    factory = MagicMock()
    save = Mock()
    consumer = ReadingConsumer("TS-01", factory, save)
    client = Mock()
    client.publish.return_value.rc = 0
    payload = dict(
        schema_version=1, sample_id=str(uuid4()), box_id="TS-01",
        sequence_no=12, profile_id=str(uuid4()), observed_at="2026-11-03T12:00:00Z",
        clock_reliable=True, temperature_c="23.45", quality="valid",
    )
    message = SimpleNamespace(topic=consumer.readings_topic, retain=False,
                              payload=json.dumps(payload).encode())
    return consumer, factory, save, client, payload, message


def test_acknowledgement_follows_successful_storage(consumer_data):
    consumer, factory, save, client, payload, message = consumer_data
    save.side_effect = lambda *args: client.publish.assert_not_called()
    consumer.on_message(client, None, message)
    save.assert_called_once()
    assert str(save.call_args.args[1].sample_id) == payload["sample_id"]
    topic, encoded = client.publish.call_args.args
    assert topic == consumer.acks_topic
    assert json.loads(encoded) == dict(schema_version=1, sample_id=payload["sample_id"], status="stored")
    assert client.publish.call_args.kwargs == dict(qos=1, retain=False)


@pytest.mark.parametrize("failure", [ValueError("conflict"), SQLAlchemyError("offline")])
def test_failed_storage_never_acknowledges(consumer_data, failure):
    consumer, factory, save, client, payload, message = consumer_data
    save.side_effect = failure
    consumer.on_message(client, None, message)
    client.publish.assert_not_called()


@pytest.mark.parametrize("case", ["topic", "box", "retained", "invalid", "large", "quality"])
def test_rejects_unauthorised_or_invalid_readings(consumer_data, case):
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
    consumer.on_message(client, None, message)
    factory.assert_not_called()
    save.assert_not_called()
    client.publish.assert_not_called()


def test_repeated_reading_is_passed_unchanged_to_idempotent_storage(consumer_data):
    consumer, factory, save, client, payload, message = consumer_data
    consumer.on_message(client, None, message)
    consumer.on_message(client, None, message)
    assert save.call_args_list[0].args[1] == save.call_args_list[1].args[1]
    assert client.publish.call_count == 2


def test_wildcard_box_configuration_is_rejected():
    with pytest.raises(ValueError):
        ReadingConsumer("+", Mock(), Mock())


@pytest.mark.parametrize("unreliable", [False, True])
def test_sensor_errors_and_unknown_times_are_preserved(consumer_data, unreliable):
    consumer, factory, save, client, payload, message = consumer_data
    payload.update(quality="sensor_error", temperature_c=None)
    if unreliable:
        payload.update(clock_reliable=False, observed_at=None)
    message.payload = json.dumps(payload).encode()
    consumer.on_message(client, None, message)
    reading = save.call_args.args[1]
    assert reading.temperature_c is None
    assert reading.clock_reliable is not unreliable
    assert (reading.observed_at is None) is unreliable
    client.publish.assert_called_once()


def test_subscription_is_renewed_after_reconnection(consumer_data):
    consumer, factory, save, client, payload, message = consumer_data
    client.subscribe.return_value = (0, 1)
    reason = SimpleNamespace(is_failure=False)
    consumer.on_connect(client, None, None, reason, None)
    consumer.on_connect(client, None, None, reason, None)
    assert client.subscribe.call_count == 2
    client.subscribe.assert_called_with(consumer.readings_topic, qos=1)


def test_subscription_denial_fails_visibly(consumer_data):
    consumer, factory, save, client, payload, message = consumer_data
    with pytest.raises(RuntimeError, match="subscription refused"):
        consumer.on_subscribe(client, None, 1, [SimpleNamespace(is_failure=True)], None)
