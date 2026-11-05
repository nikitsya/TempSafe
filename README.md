# TempSafe

TempSafe is an IoT project for monitoring temperature inside a prototype medication box. It combines a
Raspberry Pi and SCD-41 sensor, local LED feedback and a web interface for viewing readings and temperature history.
The prototype is for bench testing without real medicines; it does not determine whether medicines are suitable for use.

## Team

**Class group:** SD3a-G2

| Name              | Responsibilities                                 |
|-------------------|--------------------------------------------------|
| Nikita Smiichyk   | Backend development, database and testing        |
| Hanna Bokariuk    | Hardware, UI/UX and Universal Design             |
| Maryna Hordiienko | Frontend development, UI/UX and Universal Design |

The Scrum Master role rotates among team members. Sprint planning is maintained in Scrumwise.

## Current progress

- **Deployment:** the application is hosted at [tempsafe.app](https://tempsafe.app)
  on AWS EC2, with Caddy providing HTTPS and a reverse proxy to FastAPI.
- **Backend:** reading submission and retrieval, box information, validation, retry handling and temperature
  classification.
- **Threshold settings:** operator-token-protected backend API creates and selects versioned demo profiles;
  frontend integration, per-user permissions and device delivery remain pending. See the
  [configuration API guide](docs/api/threshold-configuration.md).
- **Database:** MySQL schema and setup scripts for the prototype box and temperature profile.
- **MQTT:** FastAPI uses FastMQTT to validate readings and acknowledge them after storage in MySQL.
  A Raspberry Pi reading reached the hosted history page on 3 November 2026 using the separate ingestion
  service. The FastMQTT deployment still needs a fresh device-to-server check. See the [MQTT guide](docs/mqtt.md).
- **Hardware:** Raspberry Pi 5 reads the SCD-41, controls the single-colour LED and passive buzzer, and saves
  readings and sensor errors to local SQLite. Integration tests are recorded; manual buzzer silencing remains planned.
- **Frontend:** dashboard and accessible history table load readings for `TS-01` from the API. The dashboard polls every
  five seconds. History refreshes when reopened.
- **UI prototype:** a separate clickable interface with synthetic data and automated browser tests.

See the [functional requirements](docs/requirements/functional-requirements.md) and
[MoSCoW priorities](docs/requirements/moscow-prioritisation.md) for the target system.

## Try the hosted application

[Open TempSafe](https://tempsafe.app) or go directly to the
[dashboard](https://tempsafe.app/pages/dashboard.html).

The dashboard refreshes automatically. Reload history to fetch new readings. Sign-in is not implemented; use test data
only.
See the [frontend guide](frontend/README.md) for current behaviour and limitations, and the
[deployment guide](docs/deployment.md) for server updates and service checks.

## Run TempSafe locally with Docker Compose

FastAPI subscribes to Mosquitto during application
start-up and serves the dashboard on port 8000. TempSafe also stores readings in MySQL before
acknowledging them. The broker is accessible within the Compose network. The hosted EC2 deployment
uses its own authenticated TLS broker and separate ingestion service.

Use Docker Compose 2.24.4 or later. Copy `.env.example` to `.env` if needed and set both MySQL
passwords. Run these commands from the project root in the same shell:

```sh
tempsafe() { docker compose -p tempsafe-local -f compose.yaml -f compose.local.yaml "$@"; }
tempsafe up --build -d --wait
tempsafe ps
```

Open the [local dashboard](http://127.0.0.1:8000/pages/dashboard.html). A fresh database volume
contains box `TS-01` and its demo profile. To check ingestion, run this subscriber in a broker shell:

```sh
tempsafe exec mosquitto mosquitto_sub -t tempsafe/boxes/TS-01/acks -q 1 -C 1
```

In a second terminal, define the same `tempsafe` function and publish a synthetic reading:

```sh
tempsafe exec mosquitto mosquitto_pub -q 1 -t tempsafe/boxes/TS-01/readings -m '{
  "schema_version":1, "sample_id":"2e8a8349-8694-47b7-8abe-284adf85738a",
  "box_id":"TS-01", "sequence_no":1, "profile_id":"e93a4368-e11a-4f27-8b31-d55d61392548",
  "observed_at":"2026-11-03T12:00:00Z", "clock_reliable":true, "temperature_c":"23.45", "quality":"valid"
}'
```

The subscriber should receive `stored` with the same sample ID. Open the [local history
page](http://127.0.0.1:8000/pages/history.html) to find the 23.45°C reading. Its fixed date makes
it suitable for checking retries. Publishing the same payload again should acknowledge the existing
record. Run `tempsafe down` to stop the services and keep its database volume.

## Backend development

Use Python 3.11 or later. From the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows, create the environment with `py -3.11 -m venv .venv` and activate it with
`.venv\Scripts\Activate.ps1` in PowerShell.

Follow the [database setup guide](database/README.md) to configure `.env`, create the tables and add the prototype box
and profile. Then follow the [backend guide](backend/temsafe/README.md) to start the server and try the API.

## Code and development guides

| Area                | Location / guide                                 |
|---------------------|--------------------------------------------------|
| Device scripts      | [device/](device/)                               |
| Backend and API     | [Backend guide](backend/temsafe/README.md)       |
| Database            | [Database setup](database/README.md)             |
| Web interface       | [Frontend guide](frontend/README.md)             |
| Clickable prototype | [Prototype guide](prototype/ui/README.md)        |
| Backend tests       | [Test instructions](tests/backend/README.md)     |
| Deployment          | [Hosting and service checks](docs/deployment.md) |

## Project documentation

| Topic                          | Documents                                                                                                                                                                                                                                                        |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Scope and requirements         | [Project scope](docs/project/project-scope.md) · [Requirements](docs/requirements/functional-requirements.md) · [Priorities](docs/requirements/moscow-prioritisation.md)                                                                                         |
| Users and scenario             | [Persona](docs/requirements/user-persona.md) · [Main use case](docs/requirements/main-use-case.md)                                                                                                                                                               |
| Interface and accessibility    | [UI design](docs/design/ui-design.md) · [Core scenario mock-ups](docs/design/core-scenario-mockups.md) · [Accessibility criteria](docs/design/accessibility-criteria.md)                                                                                         |
| Hardware                       | [Parts list](docs/hardware/hardware-parts-list.md) · [Wiring and Fritzing diagram](docs/hardware/prototype-wiring.md)                                                                                                                                            |
| Research                       | [Sensor research](docs/research/sensor-research.md) · [Database research](docs/research/database-research.md) · [All research](docs/research/)                                                                                                                   |
| Testing                        | [System test plan](docs/testing/initial-test-plan.md) · [Browser test results](docs/testing/browser-test-plan.md) · [Sensor test](docs/testing/scd41-basic-readings.md) · [LED test](docs/testing/led-patterns.md) · [Buzzer test](docs/testing/buzzer-alert.md) |
| Assessment and project records | [October G-CA1 design](docs/iot-gca/smart-box-iot-gca1-design.docx) · [Presentation materials](docs/presentation/) · [AI chat log](docs/AI_Chat_Log.md)                                                                                                          |

The Word design document, cover sheet and elevator pitch are October assessment artefacts, not current setup
instructions. They retain earlier proposals such as Pi 400, GPIO17/1 kΩ LED wiring, a 15°C lower threshold
and client-certificate MQTT authentication. Current hardware, thresholds and broker access are documented
in the guides above; the original assessment files are preserved as historical records.

## Licence

[MIT licence](LICENSE).
