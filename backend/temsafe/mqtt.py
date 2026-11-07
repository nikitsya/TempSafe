"""Receive authorised MQTT readings and acknowledge committed database records."""

import asyncio
import json
import logging
import os
import re
import ssl
from contextlib import asynccontextmanager

from fastapi_mqtt import FastMQTT, MQTTConfig
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from temsafe.schemas import ReadingCreate

LOGGER = logging.getLogger(__name__)
MAX_PAYLOAD_BYTES = 4096


class ReadingConsumer:
    """Consume one box's topics; broker ACLs must restrict their publishers."""

    def __init__(self, box_id, session_factory, save):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", box_id):
            raise ValueError("Invalid MQTT box ID")
        self.box_id = box_id
        self.readings_topic = f"tempsafe/boxes/{box_id}/readings"
        self.acks_topic = f"tempsafe/boxes/{box_id}/acks"
        self.session_factory = session_factory
        self.save = save

    def store(self, topic, payload, retained=False):
        """Validate and commit in a worker thread, returning an application acknowledgement."""
        try:
            if topic != self.readings_topic or retained:
                raise ValueError("Unexpected topic or retained reading")
            if len(payload) > MAX_PAYLOAD_BYTES:
                raise ValueError("Reading payload too large")
            reading = ReadingCreate.model_validate_json(payload)
            if reading.box_id != self.box_id:
                raise ValueError("Payload box does not match the authorised topic")
            with self.session_factory() as session:
                # save_reading commits, or returns an identical previously stored sample.
                self.save(session, reading)
        except ValueError:
            # Do not log payloads, credentials or database parameters.
            LOGGER.warning("Rejected invalid or conflicting MQTT reading")
            return
        except SQLAlchemyError:
            LOGGER.error("Database operation failed; device must retry without changing the sample")
            return

        return json.dumps({
            "schema_version": 1,
            "sample_id": str(reading.sample_id),
            "status": "stored",
        })


def create_mqtt():
    """Build the subscriber for the local Compose broker or the authenticated TLS broker."""
    enabled = os.getenv("MQTT_ENABLED", "false").lower()
    if enabled not in {"true", "false"}:
        raise ValueError("MQTT_ENABLED must be true or false")
    if enabled == "false":
        LOGGER.info("MQTT ingestion disabled; set MQTT_ENABLED=true to enable it")
        return None

    from temsafe.db.session import SessionLocal
    from temsafe.monitoring.readings import save_reading

    if os.getenv("TEMSAFE_LOCAL_MQTT") == "1":
        config = MQTTConfig(host="mosquitto", port=1883)
    else:
        for name in ("MQTT_HOST", "MQTT_PASSWORD"):
            if not os.getenv(name):
                raise ValueError(f"Set {name} before enabling MQTT")
        context = ssl.create_default_context(cafile=os.getenv("MQTT_CA_FILE") or None)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        config = MQTTConfig(
            host=os.environ["MQTT_HOST"], port=int(os.getenv("MQTT_PORT", "8883")),
            username=os.getenv("MQTT_USERNAME", "backend-ingest"),
            password=os.environ["MQTT_PASSWORD"], ssl=context,
        )
    config.reconnect_retries = -1
    config.reconnect_delay = 6
    consumer = ReadingConsumer(os.getenv("MQTT_BOX_ID", "TS-01"), SessionLocal, save_reading)
    mqtt = FastMQTT(
        config=config,
        client_id=os.getenv("MQTT_CLIENT_ID", "tempsafe-api-TS-01"),
        clean_session=True,
    )
    processing = asyncio.Lock()

    @mqtt.subscribe(consumer.readings_topic, qos=1, retain_as_published=True)
    async def receive(client, topic, payload, qos, properties):
        # Serialise database writes; synchronous MySQL work must not block the event loop.
        async with processing:
            acknowledgement = await run_in_threadpool(
                consumer.store, topic, payload, bool((properties or {}).get("retain", False))
            )
            if acknowledgement is not None:
                if not client.is_connected:
                    LOGGER.warning("MQTT disconnected before acknowledgement; device must retry")
                    return
                client.publish(consumer.acks_topic, acknowledgement, qos=1, retain=False)

    @mqtt.on_subscribe()
    def subscribed(client, mid, granted_qos, properties):
        if not granted_qos or any(code >= 128 for code in granted_qos):
            LOGGER.error("MQTT subscription refused; check broker ACLs")
        else:
            LOGGER.info("Subscribed to %s", consumer.readings_topic)

    return mqtt


@asynccontextmanager
async def lifespan(app):
    """Start and stop MQTT alongside FastAPI."""
    mqtt = create_mqtt()
    app.state.mqtt = mqtt
    try:
        if mqtt is not None:
            await asyncio.wait_for(mqtt.mqtt_startup(), timeout=15)
        yield
    finally:
        if mqtt is not None:
            await mqtt.mqtt_shutdown()
        app.state.mqtt = None
