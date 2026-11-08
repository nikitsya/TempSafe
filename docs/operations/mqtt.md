# MQTT ingestion

The MQTT broker is configured on AWS with TLS and separate accounts for the device and backend.

The Raspberry Pi publisher is implemented in [`device/mqtt_publisher.py`](../../device/mqtt_publisher.py). It sends readings from the local SQLite
database and waits for the server's storage confirmation.

The FastAPI service uses FastMQTT to receive readings and save them to MySQL. This version was
deployed on EC2 on 7 November 2026, replacing the standalone MQTT worker. The broker connection
was observed during start-up; a fresh Pi-to-MySQL reading and storage acknowledgement still need
verification. See the [deployment record](deployment.md#current-deployment--verified-8-november-2026).

On 3 November 2026, the operator reported successful authenticated message delivery and verified that anonymous
connections were rejected. Broker topic permissions were also checked: the device account could not publish to the
acknowledgement topic or another box's topic.

## Integration check — 3 November 2026

Real SCD41 readings were sent from the Raspberry Pi to the server through MQTT. The publisher received `stored`
acknowledgements.

A new reading recorded on 3 November 2026 at 23:02:57 UTC, with a temperature of 18.91°C, appeared on the History page.

This check covered the Raspberry Pi, broker, standalone MQTT worker, MySQL and web application.
It predates the FastMQTT deployment and does not verify the current ingestion service.

## Connection and permissions

- Host: `mqtt.tempsafe.app`; TCP port: `8883`.
- TLS: verify the hostname and certificate using the operating system trust store; minimum TLS 1.2.
- Device username: `device-TS-01`; supply its separate password privately.
- Backend username: `backend-ingest`; never distribute this account to devices.
- Device publishes to `tempsafe/boxes/TS-01/readings` and subscribes to `tempsafe/boxes/TS-01/acks`.
- Backend permissions are the reverse. No wildcard access is required.
- Use QoS 1 and `retain=false` for readings and acknowledgements.
- The AWS rules recorded on 3 November allow TCP 8883 from `0.0.0.0/0`, supporting
  devices that change Wi-Fi networks or use a mobile hotspot.
  TLS, device credentials and topic ACLs remain mandatory. See [network rules](deployment.md#network-access).

The broker ACL is the identity boundary: the subscriber cannot see the original publisher's username.
Only the assigned device account must have write permission for its readings topic.
The subscriber additionally checks that the payload's box ID matches that topic.

## Message contract

Publish the [ReadingCreate JSON payload](../api/api-contract.md#saving-incoming-readings) to the device's
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

## Deploy on the existing EC2 server

The hosted service is already configured. On 8 November, verification found:

- `tempsafe.service` runs FastAPI with one Uvicorn worker; the old standalone
  `tempsafe-mqtt.service` is disabled.
- `/etc/systemd/system/tempsafe.service.d/mqtt.conf` enables MQTT and loads
  `/etc/tempsafe/mqtt.env`, owned by `root:root` with mode `600`.
- The broker resolves to `127.0.0.1` on EC2, while TLS still verifies
  `mqtt.tempsafe.app`. The configured client ID is `tempsafe-ingest-TS-01`.

For future updates or reconstruction, follow the
[application update procedure](deployment.md#updating-the-application), including database backups
and required migrations. Deploy the reviewed commit to `/home/ubuntu/Smart-Box` and install its dependencies:

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

Preserve the existing `/etc/tempsafe/mqtt.env` and its credentials. If rebuilding the service,
create that file with root ownership and mode 600 using the following settings:

```dotenv
MQTT_HOST=mqtt.tempsafe.app
MQTT_PORT=8883
MQTT_USERNAME=backend-ingest
MQTT_PASSWORD=replace-with-the-backend-mqtt-password
MQTT_BOX_ID=TS-01
MQTT_CLIENT_ID=tempsafe-ingest-TS-01
```

Use the existing project's `.env` for MySQL credentials. Configure the existing FastAPI systemd service to read both
files as shown below.
Never commit either real environment file, password files or certificate private keys.

The systemd override below sets `MQTT_ENABLED=true`. Keep that switch in the override
and avoid conflicting values in the environment files.
Keep the client ID unique; another client using it can disconnect the running subscriber.

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
Edit `/etc/systemd/system/tempsafe.service.d/mqtt.conf` with `sudoedit` to match the following
override. On a new host, create the `tempsafe.service.d` directory first:

```ini
[Service]
EnvironmentFile=/etc/tempsafe/mqtt.env
Environment=MQTT_ENABLED=true
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

For local HTTP-only development, leave `MQTT_ENABLED=false` in `.env`. The
[local Compose setup](../../README.md#run-tempsafe-locally-with-docker-compose) instead enables MQTT
against an isolated broker inside the Compose network. To connect a development subscriber to
the hosted TLS broker, use separately authorised settings and a unique client ID; do not reuse
`tempsafe-ingest-TS-01` while the server is running.

The application emits `Subscribed to tempsafe/boxes/TS-01/readings` at INFO level when the broker
accepts the subscription. Whether it appears in the journal depends on the application logging
configuration. A broker connection or running service alone does not prove successful ingestion.

## Validation and remaining work

The current deployment still needs the following device integration checks:

1. Send a fresh Pi reading and match its sample ID to a `stored` acknowledgement,
   the MySQL record and the signed-in history view.
2. Retry that identical payload and confirm another acknowledgement but only one
   database record.
3. Interrupt and restore the device connection, then confirm pending SQLite
   records are retried and marked uploaded only after storage acknowledgement.

Test database failures in an isolated environment, not by stopping the hosted database.
Confirm there is no `stored` acknowledgement on failure and that an unchanged retry
succeeds after recovery.

Run the focused backend unit tests with the project's development dependencies and
required environment configured:

```bash
.venv/bin/python -m pytest tests/backend/test_mqtt.py -q
```

Unit tests cover storage before acknowledgement, failure without acknowledgement, mismatched box/topic,
invalid JSON and quality, retained and oversized payloads, repeated unchanged delivery, and wildcard configuration.
They use a mock storage boundary and do not replace the MQTT-to-MySQL integration test.

Heartbeat interval settings are stored by the API, but the current MQTT implementation only
handles readings and storage acknowledgements. Delivery of that setting and authenticated
heartbeat reporting are not implemented in this deployed revision.

HTTP publishers use a separate device key restricted to their assigned box.
See the [API authentication guide](../api/api-contract.md#authentication).
