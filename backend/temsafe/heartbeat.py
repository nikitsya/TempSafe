"""Confirm live device contact through a single-use MQTT challenge."""

import asyncio
import json
import logging
import secrets
import time
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from temsafe.models import Box

LOGGER = logging.getLogger(__name__)


class Heartbeat(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal[1]
    box_id: str
    challenge: str | None = Field(default=None, pattern="^[0-9a-f]{32}$")


class HeartbeatConsumer:
    """Keep one pending challenge for the assigned box in this subscriber."""

    def __init__(self, box_id, session_factory):
        self.box_id = box_id
        self.session_factory = session_factory
        self.topic = f"tempsafe/boxes/{box_id}/heartbeat"
        self.challenge_topic = f"tempsafe/boxes/{box_id}/challenge"
        self.challenge = None
        self.expires_at = 0.0

    def receive(self, topic, payload, retained):
        """Return a challenge on request, or commit contact after a valid echo."""
        if topic != self.topic or retained or len(payload) > 4096:
            return
        try:
            message = Heartbeat.model_validate_json(payload)
            if message.box_id != self.box_id:
                return
            with self.session_factory() as db:
                box = db.get(Box, self.box_id, with_for_update=message.challenge is not None)
                if box is None:
                    return
                now = time.monotonic()
                if message.challenge is None:
                    if self.challenge is None or now >= self.expires_at:
                        self.challenge = secrets.token_hex(16)
                        self.expires_at = now + 30
                    return json.dumps({
                        "schema_version": 1, "box_id": self.box_id, "challenge": self.challenge,
                        "heartbeat_interval_seconds": box.heartbeat_interval_seconds,
                    })
                if self.challenge != message.challenge or now >= self.expires_at:
                    return
                box.last_seen_at = datetime.now(UTC).replace(tzinfo=None)
                db.commit()
                self.challenge = None
        except ValueError:
            LOGGER.warning("Rejected malformed heartbeat")
        except SQLAlchemyError:
            LOGGER.error("Heartbeat database operation failed")


def subscribe_heartbeats(mqtt, box_id, session_factory):
    consumer = HeartbeatConsumer(box_id, session_factory)
    lock = asyncio.Lock()

    @mqtt.subscribe(consumer.topic, qos=1, retain_as_published=True)
    async def heartbeat(client, topic, payload, qos, properties):
        async with lock:
            challenge = await run_in_threadpool(
                consumer.receive, topic, payload, bool((properties or {}).get("retain", False))
            )
            if challenge is not None and client.is_connected:
                client.publish(consumer.challenge_topic, challenge, qos=1, retain=False)
