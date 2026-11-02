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
- **Database:** MySQL schema and setup scripts for the prototype box and temperature profile.
- **Hardware:** Raspberry Pi 5 reads the SCD-41, controls the single-colour LED and passive buzzer, and saves
  readings and sensor errors to local SQLite. Integration tests are recorded; manual buzzer silencing remains planned.
- **Frontend:** dashboard with sample data, a sign-in form and a history placeholder. Live data integration remains
  planned.
- **UI prototype:** a separate clickable interface with synthetic data and automated browser tests.

Device-to-backend communication, reliable offline upload and acknowledgement, authentication and phone notifications
remain planned.
See the [functional requirements](docs/requirements/functional-requirements.md) and
[MoSCoW priorities](docs/requirements/moscow-prioritisation.md) for the target system.

## Try the hosted application

[Open TempSafe](https://tempsafe.app) or go directly to the
[dashboard](https://tempsafe.app/pages/dashboard.html).

This is the application frontend served by the backend. The sign-in form is not connected to authentication,
the dashboard uses sample data and the history page is a placeholder. "API connected" confirms that the
backend health endpoint responds; it does not confirm a database connection or live sensor readings.
Use test data only while authentication remains unimplemented.

See the [deployment notes](docs/deployment.md) for the hosting setup and service checks.

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
| Assessment and project records | [Presentation materials](docs/presentation/) · [AI chat log](docs/AI_Chat_Log.md)                                                                                                                                                                                |

## Licence

[MIT licence](LICENSE).
