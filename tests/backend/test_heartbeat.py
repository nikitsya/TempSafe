"""Exercise MQTT heartbeat challenges against transactional MySQL records."""

import json
from contextlib import nullcontext
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from temsafe.database import engine
from temsafe.heartbeat import HeartbeatConsumer
from temsafe.models import Box


@pytest.fixture
def heartbeat_box():
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
                box_id = str(uuid4())
                box = Box(box_id=box_id, name="Heartbeat test", heartbeat_interval_seconds=120)
                db.add(box)
                db.commit()
                yield HeartbeatConsumer(box_id, lambda: nullcontext(db)), box
        finally:
            transaction.rollback()


def packet(box_id, **fields):
    return json.dumps({"schema_version": 1, "box_id": box_id, **fields}).encode()


def test_single_use_challenge_records_contact(heartbeat_box):
    consumer, box = heartbeat_box
    request = packet(box.box_id)
    response = json.loads(consumer.receive(consumer.topic, request, False))
    assert response["heartbeat_interval_seconds"] == 120
    assert json.loads(consumer.receive(consumer.topic, request, False)) == response
    assert box.last_seen_at is None
    echo = packet(box.box_id, challenge=response["challenge"])
    consumer.receive(consumer.topic, echo, True)
    consumer.receive(consumer.topic, packet("another-box", challenge=response["challenge"]), False)
    consumer.receive(consumer.topic, packet(box.box_id, challenge="0" * 32), False)
    assert box.last_seen_at is None
    consumer.receive(consumer.topic, echo, False)
    seen = box.last_seen_at
    assert isinstance(seen, datetime)
    consumer.receive(consumer.topic, echo, False)
    assert box.last_seen_at == seen


def test_expired_and_pre_restart_challenges_do_not_refresh_contact(heartbeat_box, monkeypatch):
    consumer, box = heartbeat_box
    clock = Mock(side_effect=[1, 31, 32])
    monkeypatch.setattr("temsafe.heartbeat.time", Mock(monotonic=clock))
    reply = json.loads(consumer.receive(consumer.topic, packet(box.box_id), False))
    echo = packet(box.box_id, challenge=reply["challenge"])
    consumer.receive(consumer.topic, echo, False)
    restarted = HeartbeatConsumer(box.box_id, consumer.session_factory)
    restarted.receive(restarted.topic, echo, False)
    assert box.last_seen_at is None


@pytest.mark.parametrize("topic,payload,retained", [
    ("tempsafe/boxes/other/heartbeat", packet("TS-01"), False),
    ("tempsafe/boxes/TS-01/heartbeat", packet("TS-01"), True),
    ("tempsafe/boxes/TS-01/heartbeat", packet("other"), False),
    ("tempsafe/boxes/TS-01/heartbeat", b"invalid", False),
    ("tempsafe/boxes/TS-01/heartbeat", b" " * 4097, False),
])
def test_invalid_heartbeats_do_not_open_database(topic, payload, retained):
    factory = Mock()
    assert HeartbeatConsumer("TS-01", factory).receive(topic, payload, retained) is None
    factory.assert_not_called()
