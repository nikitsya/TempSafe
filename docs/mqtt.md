# MQTT ingestion

The MQTT broker is configured on AWS with TLS and separate accounts for the device and backend.

The Raspberry Pi publisher is implemented in `device/mqtt_publisher.py`. It sends readings from the local SQLite
database and waits for the server's storage confirmation.

The FastAPI service uses FastMQTT to receive readings and save them to MySQL. Deployment and an end-to-end check of this version on EC2 are pending.

On 3 November 2026, the operator reported successful authenticated message delivery and verified that anonymous
connections were rejected. Broker topic permissions were also checked: the device account could not publish to the
acknowledgement topic or another box's topic.

## Integration check — 3 November 2026

Real SCD41 readings were sent from the Raspberry Pi to the server through MQTT. The publisher received `stored`
acknowledgements.

A new reading recorded on 3 November 2026 at 23:02:57 UTC, with a temperature of 18.91°C, appeared on the History page.

This check covered the Raspberry Pi, broker, standalone MQTT worker, MySQL and web application. Repeat it after deploying the FastMQTT subscriber.

## Connection and permissions

- Host: `mqtt.tempsafe.app`; TCP port: `8883`.
- TLS: verify the hostname and certificate using the operating system trust store; minimum TLS 1.2.
- Device username: `device-TS-01`; supply its separate password privately.
- Backend username: `backend-ingest`; never distribute this account to devices.
- Device publishes to `tempsafe/boxes/TS-01/readings` and subscribes to `tempsafe/boxes/TS-01/acks`.
- Backend permissions are the reverse. No wildcard access is required.
- Use QoS 1 and `retain=false` for readings and acknowledgements.
- AWS permits TCP 8883 from `0.0.0.0/0` so the Pi can change Wi-Fi networks or use a mobile hotspot.
  TLS, device credentials and topic ACLs remain mandatory. See [network rules](deployment.md#network-access).

The broker ACL is the identity boundary: the subscriber cannot see the original publisher's username.
Only the assigned device account must have write permission for its readings topic.
The subscriber additionally checks that the payload's box ID matches that topic.

## Message contract

Publish the [ReadingCreate JSON payload](api/api-contract.md#saving-incoming-readings) to the device's
readings topic, with a maximum MQTT payload of 4096 bytes. The box and profile must already exist in
MySQL. Preserve the sample UUID, persistent sequence and observation time on every retry.

After a database commit, or an identical retry of a stored record, the subscriber publishes:

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
network loss, and retry pending records after either device or subscriber restarts.

The subscriber uses clean MQTT sessions: the local device outbox and application retries are required
when the subscriber is offline. QoS 1 alone does not guarantee database delivery.
Invalid data, unknown references, conflicting retries and database failures receive no `stored`
acknowledgement. Preserve those records and investigate subscriber logs rather than deleting them or
generating replacement identifiers. Retained messages are not supported.

## Device heartbeat contract

The TLS subscriber accepts live contact independently of temperature samples.
Before enabling this on a broker, grant the assigned device write access to its
`heartbeat` topic and read access to its `challenge` topic. Grant the backend
the reverse permissions and keep both topics private to those accounts. These
grants are in addition to the existing readings and acknowledgement grants.
The anonymous local Compose broker skips heartbeat processing.

1. The Pi subscribes to `tempsafe/boxes/TS-01/challenge` before publishing.
2. To request a challenge, publish `{"schema_version":1,"box_id":"TS-01"}` to
   `tempsafe/boxes/TS-01/heartbeat`. Use QoS 1 and retain=false for the exchange.
3. The backend replies on the challenge topic with `schema_version`, `box_id`,
   a random `challenge` and the desired `heartbeat_interval_seconds`. The device
   echoes only the version, box ID and challenge on the heartbeat topic within
   30 seconds. Repeated requests within that window share the outstanding challenge.
4. After verifying the echo, the backend records server UTC in `boxes.last_seen_at`.
   The signed-in box details endpoint exposes that time. The device should start
   a fresh exchange at the desired interval even when the sensor fails. Discard
   expired challenges on reconnect rather than placing heartbeats in the readings outbox.

A duplicate echo, a retained message or an echo from before a subscriber restart
cannot refresh contact. The single-worker subscriber keeps challenges in memory.
The Pi exchange and production broker grants require a separate deployment check.

## Deploy on the existing EC2 server

First transfer the reviewed code to `/home/ubuntu/Smart-Box` and install its dependencies:

```bash
cd /home/ubuntu/Smart-Box
.venv/bin/python -m pip install -e .
```

The subscriber on EC2 should reach the broker through loopback while still verifying its public TLS name.
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
MQTT_CLIENT_ID=tempsafe-api-TS-01
```

Use the existing project's `.env` for MySQL credentials. Configure the existing FastAPI systemd service to read both
files as shown below.
Never commit either real environment file, password files or certificate private keys.

Add these settings to `/etc/tempsafe/mqtt.env` alongside the credentials above:

```dotenv
MQTT_ENABLED=true
MQTT_CLIENT_ID=tempsafe-api-TS-01
```

FastMQTT starts and stops with FastAPI using `lifespan`, and registers the readings handler with
`@mqtt.subscribe(...)`. Database writes run in a thread so they do not block HTTP requests.
TLS certificate and hostname verification remain enabled. Initial connection failure or a 15-second
startup timeout prevents application startup; systemd retries the service. After a lost connection,
the client retries indefinitely and renews its subscription.

Stop the old standalone service if it was installed:

```bash
sudo systemctl disable --now tempsafe-mqtt.service
```

If systemd reports that the old unit does not exist, continue. Do not run both consumers.
Run `sudo systemctl edit tempsafe.service` and add:

```ini
[Service]
EnvironmentFile=/etc/tempsafe/mqtt.env
ExecStart=
ExecStart=/home/ubuntu/Smart-Box/.venv/bin/python -m uvicorn temsafe.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5
```

Keep the existing working directory and database environment settings. Use exactly one Uvicorn worker
and no production reload: each process creates its own MQTT client.

```bash
sudo systemctl daemon-reload
sudo systemctl restart tempsafe
sudo systemctl status tempsafe --no-pager -l
sudo journalctl -u tempsafe -n 30 --no-pager
```

For local HTTP-only development, leave `MQTT_ENABLED=false` in `.env`. To test ingestion locally,
set it to `true` and supply the MQTT settings using a separate authorised client identity; do not
connect using the production client ID while the server is running.

Expected log: `Broker accepted MQTT subscription`. A running service alone does not prove
successful ingestion. Submit a valid test record, observe `stored`, check the same sample in MySQL,
and repeat the identical message to verify that there is only one database record. Also verify a
database failure produces no `stored`, followed by a successful unchanged retry after recovery.

## Validation and remaining work

```bash
.venv/bin/python -m pytest tests/backend/test_mqtt.py -q
```

Unit tests cover storage before acknowledgement, failure without acknowledgement, mismatched box/topic,
invalid JSON and quality, retained and oversized payloads, repeated unchanged delivery, and wildcard configuration.
They use a mock storage boundary and do not replace the MQTT-to-MySQL integration test.

HTTP publishers use a separate device key restricted to their assigned box.
See the [API authentication guide](api/api-contract.md#authentication).
