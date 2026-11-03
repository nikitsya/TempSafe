# MQTT ingestion

The broker has been configured on AWS with TLS and separate device and backend accounts.
The operator reported successful connectivity, authenticated message delivery in both directions,
and refusal of device publishing to the acknowledgement topic and another box's topic.
The ingestion worker is implemented locally; AWS deployment and a real MQTT-to-MySQL test are still pending.
The Raspberry Pi publisher and application acknowledgement handling are not yet implemented.

## Connection and permissions

- Host: `mqtt.tempsafe.app`; TCP port: `8883`.
- TLS: verify the hostname and certificate using the operating system trust store; minimum TLS 1.2.
- Device username: `device-TS-01`; supply its separate password privately.
- Backend username: `backend-ingest`; never distribute this account to devices.
- Device publishes to `tempsafe/boxes/TS-01/readings` and subscribes to `tempsafe/boxes/TS-01/acks`.
- Backend permissions are the reverse. No wildcard access is required.
- Use QoS 1 and `retain=false` for readings and acknowledgements.
- AWS currently permits port 8883 from the operator's public IP. Add the Raspberry Pi network's public
  IP before testing from the device; do not open unencrypted port 1883.

The broker ACL is the identity boundary: the worker cannot see the original publisher's username.
Only the assigned device account must have write permission for its readings topic.
The worker additionally checks that the payload's box ID matches that topic.

## Message contract

The payload uses the same validation as `POST /api/readings`, with a maximum MQTT payload of 4096 bytes:

```json
{
  "schema_version": 1,
  "sample_id": "2e8a8349-8694-47b7-8abe-284adf85738a",
  "box_id": "TS-01",
  "sequence_no": 1,
  "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
  "observed_at": "2026-11-03T12:00:00Z",
  "clock_reliable": true,
  "temperature_c": 23.45,
  "quality": "valid"
}
```

The box and its profile must already exist in MySQL. Use each real sample's UUID and persistent
sequence number, not the example identifiers. Sequence numbers must not restart after a device reboot.
For a sensor error, use `quality: "sensor_error"` and `temperature_c: null`.
For an unreliable clock, use `clock_reliable: false` and `observed_at: null`.

After a database commit, or an identical retry of a stored record, the worker publishes:

```json
{
  "schema_version": 1,
  "sample_id": "2e8a8349-8694-47b7-8abe-284adf85738a",
  "status": "stored"
}
```

The device must subscribe before publishing and keep its SQLite record pending until it receives
this acknowledgement for that sample ID. MQTT PUBACK only confirms broker receipt, not database storage.
If the application acknowledgement is missing, retry with bounded backoff and the unchanged payload,
including observation time, sample ID, profile ID and sequence number. Reconnect and resubscribe after
network loss, and retry pending records after either device or worker restarts.

The worker uses clean MQTT sessions: the local device outbox and application retries are required
when the worker is offline. QoS 1 alone does not guarantee database delivery.
Invalid data, unknown references, conflicting retries and database failures receive no `stored`
acknowledgement. Preserve those records and investigate worker logs rather than deleting them or
generating replacement identifiers. Retained messages are not supported.

## Deploy on the existing EC2 server

First transfer the reviewed code to `/home/ubuntu/Smart-Box` and install its dependencies:

```bash
cd /home/ubuntu/Smart-Box
.venv/bin/python -m pip install -e .
```

The worker on EC2 should reach the broker through loopback while still verifying its public TLS name.
In `/etc/hosts` on EC2 only, add the following mapping if it is not already present:

```text
127.0.0.1 mqtt.tempsafe.app
```

Keep public DNS pointing to the EC2 public address. Verify the server's local resolution with
`getent ahostsv4 mqtt.tempsafe.app`. This avoids depending on access to the public port from the server itself.

Create `/etc/tempsafe/mqtt.env`, owned by root with mode 600, containing:

```dotenv
MQTT_HOST=mqtt.tempsafe.app
MQTT_PORT=8883
MQTT_USERNAME=backend-ingest
MQTT_PASSWORD=replace-with-the-backend-mqtt-password
MQTT_BOX_ID=TS-01
MQTT_CLIENT_ID=tempsafe-ingest-TS-01
```

Use the existing project's `.env` for MySQL credentials. The systemd service reads both files.
Never commit either real environment file, password files or certificate private keys.

```bash
sudo install -m 644 deploy/tempsafe-mqtt.service /etc/systemd/system/tempsafe-mqtt.service
sudo systemctl daemon-reload
sudo systemctl enable --now tempsafe-mqtt
sudo systemctl status tempsafe-mqtt --no-pager -l
sudo journalctl -u tempsafe-mqtt -n 30 --no-pager
```

Expected log: `Subscribed to tempsafe/boxes/TS-01/readings`. A running service alone does not prove
successful ingestion. Submit a valid test record, observe `stored`, check the same sample in MySQL,
and repeat the identical message to verify that there is only one database record. Also verify a
database failure produces no `stored`, followed by a successful unchanged retry after recovery.

## Validation and remaining work

```bash
.venv/bin/python -m pytest tests/backend/test_mqtt_worker.py -q
```

Unit tests cover storage before acknowledgement, failure without acknowledgement, mismatched box/topic,
invalid JSON and quality, retained and oversized payloads, repeated unchanged delivery, and wildcard configuration.
They use a mock storage boundary and do not replace the MQTT-to-MySQL integration test.

MQTT security does not secure the existing HTTP reading endpoint. API authentication and authorisation
remain separate required work. The dashboard still uses sample data and history is a placeholder.
