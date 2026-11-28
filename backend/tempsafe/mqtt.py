"""Receive authorised MQTT readings and acknowledge committed database records."""

import asyncio
import json
import logging
import os
import re
import ssl
from uuid import UUID

from fastapi_mqtt import FastMQTT, MQTTConfig
from pydantic import BaseModel, ConfigDict, StrictInt
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from tempsafe.db.models import BoxConfiguration
from tempsafe.db.session import AsyncSessionLocal
from tempsafe.monitoring.readings import save_reading
from tempsafe.schemas import ReadingCreate
from tempsafe.settings import project_setting

LOGGER = logging.getLogger(__name__)
MAX_PAYLOAD_BYTES = 4096


class AppliedConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: StrictInt
    box_id: str
    profile_id: UUID


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

    async def store(self, topic, payload, retained=False) -> str | None:
        """Return the acknowledgement after storage succeeds, or None on rejection or failure."""
        try:
            if topic != self.readings_topic or retained:
                raise ValueError("Unexpected topic or retained reading")
            if len(payload) > MAX_PAYLOAD_BYTES:
                raise ValueError("Reading payload too large")
            reading = ReadingCreate.model_validate_json(payload)
            if reading.box_id != self.box_id:
                raise ValueError("Payload box does not match the authorised topic")
            async with self.session_factory() as session:
                # save_reading commits, or returns an identical previously stored sample.
                await self.save(session, reading)
        except ValueError:
            # Do not log payloads, credentials or database parameters.
            LOGGER.warning("Rejected invalid or conflicting MQTT reading")
            return None
        except SQLAlchemyError:
            LOGGER.error("Database operation failed; device must retry without changing the sample")
            return None

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

    if project_setting("TEMPSAFE_LOCAL_MQTT") == "1":
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
    consumer = ReadingConsumer(os.getenv("MQTT_BOX_ID", "TS-01"), AsyncSessionLocal, save_reading)
    mqtt = FastMQTT(
        config=config,
        client_id=os.getenv("MQTT_CLIENT_ID", "tempsafe-api-TS-01"),
        clean_session=True,
    )
    processing = asyncio.Lock()

    @mqtt.subscribe(consumer.readings_topic, qos=1, retain_as_published=True)
    async def receive(client, topic, payload, _qos, properties):
        async with processing:
            acknowledgement = await consumer.store(topic, payload, bool((properties or {}).get("retain", False)))
            if acknowledgement is not None:
                if not client.is_connected:
                    LOGGER.warning("MQTT disconnected before acknowledgement; device must retry")
                    return
                client.publish(consumer.acks_topic, acknowledgement, qos=1, retain=False)

    applied_topic = f"tempsafe/boxes/{consumer.box_id}/configuration/applied"

    @mqtt.subscribe(applied_topic, qos=1, retain_as_published=True)
    async def confirm_profile(_client, topic, payload, _qos, properties):
        if topic != applied_topic or (properties or {}).get("retain") or len(payload) > MAX_PAYLOAD_BYTES:
            return
        try:
            report = AppliedConfiguration.model_validate_json(payload)
            if report.schema_version != 1 or report.box_id != consumer.box_id:
                return
            profile_id = str(report.profile_id)
            async with AsyncSessionLocal.begin() as db:
                # A delayed confirmation cannot override a newer selection.
                await db.execute(update(BoxConfiguration).where(
                    BoxConfiguration.box_id == consumer.box_id,
                    BoxConfiguration.profile_id == profile_id,
                ).values(applied_profile_id=profile_id))
        except ValueError:
            LOGGER.warning("Rejected invalid MQTT configuration confirmation")
        except SQLAlchemyError:
            LOGGER.error("Could not record confirmation; periodic configuration delivery will retry")

    @mqtt.on_subscribe()
    def subscribed(_client, _mid, granted_qos, _properties):
        if not granted_qos or any(code >= 128 for code in granted_qos):
            LOGGER.error("MQTT subscription refused; check broker ACLs")
        else:
            LOGGER.info("Subscribed to %s", consumer.readings_topic)

    return mqtt
