# Smart Box — TempSafe

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

- **Backend:** reading submission and retrieval, box information, validation, retry handling and temperature
  classification.
- **Database:** MySQL schema and setup scripts for the prototype box and temperature profile.
- **Hardware:** separate sensor-reading and LED-pattern tests completed; combined operation remains to be implemented.
- **Frontend:** dashboard with sample data, a sign-in form and a history placeholder. Live data integration remains
  planned.
- **UI prototype:** a separate clickable interface with synthetic data and automated browser tests.

Device-to-backend communication, offline queuing, authentication and phone notifications remain planned.
See the [functional requirements](docs/requirements/functional-requirements.md) and
[MoSCoW priorities](docs/requirements/moscow-prioritisation.md) for the target system.

## Try the UI prototype

[Open the clickable prototype](https://nikitsya.github.io/Smart-Box/prototype/ui/login.html).
Test account: `paramedic` / `demo`. This prototype uses synthetic data and does not connect to the backend.

See the [prototype guide](prototype/ui/README.md) for its pages and browser tests.

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

| Area                | Location / guide                             |
|---------------------|----------------------------------------------|
| Device scripts      | [device/](device/)                           |
| Backend and API     | [Backend guide](backend/temsafe/README.md)   |
| Database            | [Database setup](database/README.md)         |
| Web interface       | [Frontend guide](frontend/README.md)         |
| Clickable prototype | [Prototype guide](prototype/ui/README.md)    |
| Backend tests       | [Test instructions](tests/backend/README.md) |

## Project documentation

| Topic                          | Documents                                                                                                                                                                                                          |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Scope and requirements         | [Project scope](docs/project/project-scope.md) · [Requirements](docs/requirements/functional-requirements.md) · [Priorities](docs/requirements/moscow-prioritisation.md)                                           |
| Users and scenario             | [Persona](docs/requirements/user-persona.md) · [Main use case](docs/requirements/main-use-case.md)                                                                                                                 |
| Interface and accessibility    | [UI design](docs/design/ui-design.md) · [Core scenario mock-ups](docs/design/core-scenario-mockups.md) · [Accessibility criteria](docs/design/accessibility-criteria.md)                                           |
| Hardware                       | [Parts list](docs/hardware/hardware-parts-list.md) · [Wiring and Fritzing diagram](docs/hardware/prototype-wiring.md)                                                                                              |
| Research                       | [Sensor research](docs/research/sensor-research.md) · [Database research](docs/research/database-research.md) · [All research](docs/research/)                                                                     |
| Testing                        | [System test plan](docs/testing/initial-test-plan.md) · [Browser test results](docs/testing/browser-test-plan.md) · [Sensor test](docs/testing/scd41-basic-readings.md) · [LED test](docs/testing/led-patterns.md) |
| Assessment and project records | [IoT G-CA1 design](docs/project/iot-gca1-design.md) · [Presentation materials](docs/presentation/) · [AI chat log](AI_Chat_Log.md)                                                                                 |

## Licence

[MIT licence](LICENSE).
