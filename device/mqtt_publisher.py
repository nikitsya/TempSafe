import json
import os
import paho.mqtt.client as mqtt
import ssl
from queue import SimpleQueue, Empty
from sqlalchemy import select, update
from threading import Event
from time import monotonic, sleep
from uuid import UUID

from database import SessionLocal
from models import Reading

BOX_ID = "TS-01"
MQTT_HOST = "mqtt.tempsafe.app"
MQTT_PORT = 8883
MQTT_USERNAME = "device-TS-01"

READINGS_TOPIC = f"tempsafe/boxes/{BOX_ID}/readings"
ACKS_TOPIC = f"tempsafe/boxes/{BOX_ID}/acks"

subscription_ready = Event()


def on_connect(client, userdata, flags, reason_code, properties):
    subscription_ready.clear()

    if reason_code.is_failure:
        print("MQTT connection failed:", reason_code)
        return

    print("Connected to MQTT broker")
    result, _ = client.subscribe(ACKS_TOPIC, qos=1)

    if result != mqtt.MQTT_ERR_SUCCESS:
        print("Could not request acknowledgement subscription")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    if not reason_codes or any(code.is_failure for code in reason_codes):
        print("Acknowledgement subscription rejected")
        return

    subscription_ready.set()
    print("Ready to receive acknowledgements")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    subscription_ready.clear()
    print("MQTT disconnected:", reason_code)


acknowledgements = SimpleQueue()


def on_message(client, userdata, message):
    if message.topic != ACKS_TOPIC or message.retain:
        return

    if len(message.payload) > 4096:
        return

    try:
        ack = json.loads(message.payload)

        if not isinstance(ack, dict):
            return

        if type(ack.get("schema_version")) is not int:
            return

        if ack["schema_version"] != 1 or ack.get("status") != "stored":
            return

        sample_id = str(UUID(ack["sample_id"]))

    except (ValueError, TypeError, KeyError, AttributeError):
        print("Invalid acknowledgement ignored")
        return

    acknowledgements.put(sample_id)


def make_payload(reading):
    return json.dumps({
        "schema_version": 1,
        "sample_id": reading.sample_id,
        "box_id": reading.box_id,
        "sequence_no": reading.sequence_no,
        "profile_id": reading.profile_id,
        "observed_at": (
            reading.observed_at if reading.clock_reliable else None
        ),
        "clock_reliable": bool(reading.clock_reliable),
        "temperature_c": reading.temperature_c,
        "quality": reading.quality,
    }, allow_nan=False)


def create_client():
    password = os.environ.get("MQTT_PASSWORD")
    if not password:
        raise RuntimeError("MQTT_PASSWORD is not set")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"tempsafe-device-{BOX_ID}",
        protocol=mqtt.MQTTv5,
    )

    client.username_pw_set(MQTT_USERNAME, password)

    tls = ssl.create_default_context()
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    client.tls_set_context(tls)

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect_timeout = 10
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    return client


def get_pending_reading():
    with SessionLocal() as session:
        reading = session.scalar(
            select(Reading)
            .where(
                Reading.uploaded == 0,
                Reading.box_id == BOX_ID,
            )
            .order_by(Reading.sequence_no)
            .limit(1)
        )

        if reading is None:
            return None

        return reading.sample_id, make_payload(reading)


def mark_uploaded(sample_id):
    with SessionLocal.begin() as session:
        session.execute(
            update(Reading)
            .where(
                Reading.sample_id == sample_id,
                Reading.box_id == BOX_ID,
                Reading.uploaded == 0,
            )
            .values(uploaded=1)
        )

    print("Server confirmed storage:", sample_id)


def send_and_wait(client, sample_id, payload):
    result = client.publish(
        READINGS_TOPIC,
        payload,
        qos=1,
        retain=False,
    )

    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        print("Publish failed; record remains pending")
        return False

    deadline = monotonic() + 15

    while subscription_ready.is_set():
        remaining = deadline - monotonic()
        if remaining <= 0:
            break

        try:
            acknowledged_id = acknowledgements.get(
                timeout=min(remaining, 1)
            )
        except Empty:
            continue

        if acknowledged_id == sample_id:
            mark_uploaded(sample_id)
            return True

    print("No storage confirmation; record remains pending")
    return False


def main():
    client = create_client()
    retry_delay = 2

    client.connect_async(MQTT_HOST, MQTT_PORT)
    client.loop_start()

    try:
        while True:
            if not subscription_ready.wait(timeout=1):
                continue

            pending = get_pending_reading()

            if pending is None:
                sleep(1)
                continue

            sample_id, payload = pending

            if send_and_wait(client, sample_id, payload):
                retry_delay = 2
            else:
                sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

    except KeyboardInterrupt:
        print("Publisher stopped.")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
