"""Receive authorised MQTT readings and acknowledge committed database records."""

import json
import logging
import os
import re
import signal
import ssl

import paho.mqtt.client as mqtt
from sqlalchemy.exc import SQLAlchemyError

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

    def on_connect(self, client, userdata, flags, reason, properties):
        if reason.is_failure:
            LOGGER.error("MQTT connection refused: %s", reason)
            return
        result, _ = client.subscribe(self.readings_topic, qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError("Could not request MQTT subscription")

    def on_subscribe(self, client, userdata, mid, reasons, properties):
        if not reasons or any(reason.is_failure for reason in reasons):
            raise RuntimeError("MQTT subscription refused; check broker ACLs")
        LOGGER.info("Subscribed to %s", self.readings_topic)

    def on_message(self, client, userdata, message):
        try:
            if message.topic != self.readings_topic or message.retain:
                raise ValueError("Unexpected topic or retained reading")
            if len(message.payload) > MAX_PAYLOAD_BYTES:
                raise ValueError("Reading payload too large")
            reading = ReadingCreate.model_validate_json(message.payload)
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

        acknowledgement = json.dumps({
            "schema_version": 1,
            "sample_id": str(reading.sample_id),
            "status": "stored",
        })
        result = client.publish(self.acks_topic, acknowledgement, qos=1, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            LOGGER.warning("Acknowledgement not queued; an identical retry is safe")


def main():
    """Run separately from Uvicorn, with TLS verification and reconnect support."""
    from temsafe.database import SessionLocal
    from temsafe.readings import save_reading

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    password = os.environ.get("MQTT_PASSWORD")
    if not password:
        raise ValueError("Set MQTT_PASSWORD for the backend-ingest account")

    consumer = ReadingConsumer(os.getenv("MQTT_BOX_ID", "TS-01"), SessionLocal, save_reading)
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=os.getenv("MQTT_CLIENT_ID", "tempsafe-ingest-TS-01"),
        protocol=mqtt.MQTTv5,
    )
    client.username_pw_set(os.getenv("MQTT_USERNAME", "backend-ingest"), password)
    context = ssl.create_default_context(cafile=os.getenv("MQTT_CA_FILE") or None)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    client.tls_set_context(context)
    client.connect_timeout = 10
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.on_connect = consumer.on_connect
    client.on_subscribe = consumer.on_subscribe
    client.on_message = consumer.on_message

    def stop(signum, frame):
        client.disconnect()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    client.connect_async(os.environ["MQTT_HOST"], int(os.getenv("MQTT_PORT", "8883")))
    try:
        client.loop_forever(retry_first_connection=True)
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
