# Smart Box

**Class Group:** SD3a-G2  
**Team Size:** 3 members

**Documentation last updated:** 5 October 2026

## Team Members

| Name              | Responsibilities                                     |
|-------------------|------------------------------------------------------|
| Nikita Smiichyk   | Backend Development, Database, Testing               |
| Hanna Bokariuk    | UI/UX Design, Universal Design, Hardware             |
| Maryna Hordiienko | Frontend Development, UI/UX Design, Universal Design |

*The Scrum Master role rotates among team members.*

## Project Idea

Smart Box is a project designed to help paramedics monitor the temperature inside a portable box used to carry
medicines. It gives staff a clearer view of the conditions inside the box during a shift and highlights when the
temperature moves outside the range set for its contents.

## The Problem

Medicines have specific storage requirements. A portable medication box can move between a station, a vehicle and the
place where a patient needs help. Conditions around the box can change during this journey.

Knowing the temperature at one moment does not show what happened earlier. Staff may need to review whether the box
experienced a temperature change and when it occurred.

## Our Solution

The planned prototype will monitor the temperature inside the box, keep a history of sample attempts and warn when a
valid reading falls outside a configured temperature profile. Staff will be able to check the latest information and
review earlier changes.

For example, if the temperature rises above the set limit during a shift, the system highlights the change. The
responsible person can check the box and follow their service's procedures. The recorded history remains available for
later review.

## Planned Features

- User sign-in and access restricted to assigned boxes.
- One internal temperature sensor, with proposed sampling every 30 seconds.
- Current temperature, observation time and device contact time shown separately, with explicit unknown, stale and
  sensor-error states.
- Configured, versioned lower and upper temperature limits retained with each observation.
- A local warning LED that works during a network outage, with a distinct sensor-error indication.
- Temperature history presented as a graph and readable table, including gaps and out-of-range observations.
- A durable local queue for at least 24 hours of sample attempts, with retries that do not create duplicate records.
- Accessible controls and warnings that use text and symbols as well as colour.

## Proposed Architecture

| Component             | Proposed technology      | Purpose                                                                       |
|-----------------------|--------------------------|-------------------------------------------------------------------------------|
| Sensor and controller | DHT22 and Raspberry Pi   | Measure the internal temperature and operate the local warning LED.           |
| Device software       | Python                   | Record sample attempts, apply the temperature profile and upload data.        |
| Offline storage       | SQLite                   | Retain pending observations until the backend acknowledges receipt.           |
| Backend               | Python with FastAPI      | Authenticate users and devices, validate uploads and enforce box permissions. |
| Central storage       | MySQL with InnoDB        | Store boxes, profiles, access permissions and temperature history.            |
| Web application       | HTML, CSS and JavaScript | Display temperature, freshness, warnings and history.                         |
| Communication         | HTTPS with JSON payloads | Transfer observations from the device to the backend.                         |

The Raspberry Pi will sample and queue data locally before sending it to the API. The web application will retrieve
data through the backend. Delayed uploads will retain their original observation times and enrich history without
replacing a newer current state.

## Prototype Boundaries

The prototype is intended for bench demonstration and testing with no real medicines. It will not provide automatic
cooling, GPS tracking, box-opening detection, patient records or integration with ambulance-service clinical systems.
It will not replace official controlled-drug records or be deployed in a clinical environment.

Temperature limits will be configured through versioned profiles. The sensor research describes a proposed 25°C upper
limit and a project-defined 24°C early warning; these are prototype research settings, not a universal medicine storage
range. The functional requirements define classification against the configured lower and upper limits.

## Repository Structure

| Directory   | Intended contents                                            | Current state                                                 |
|-------------|--------------------------------------------------------------|---------------------------------------------------------------|
| `docs/`     | Planning, requirements, hardware and research documentation. | Documentation available.                                      |
| `device/`   | Raspberry Pi sampling, local warnings and offline queue.     | Empty; implementation planned.                                |
| `backend/`  | API, authentication and data validation.                     | Empty; implementation planned.                                |
| `database/` | Schema, migrations and database scripts.                     | Empty; example SQL is in the database research document.      |
| `frontend/` | Web dashboard and accessible history views.                  | Empty; implementation planned.                                |
| `tests/`    | Device, API, data recovery and interface tests.              | Empty; test evidence is planned in the requirements document. |

## Project Documentation

Documentation is organised by purpose and uses lower-case, hyphen-separated filenames:

- `docs/project/`: project scope, delivery schedule and milestones.
- `docs/requirements/`: user needs, required system behaviour and acceptance criteria.
- `docs/hardware/`: prototype components and hardware documentation.
- `docs/research/`: evidence, technology comparisons and proposed technical decisions.

| Document                                                                              | Contents                                                                  |
|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [Project scope](docs/project/project-scope.md)                                        | What the prototype includes and excludes.                                 |
| [Functional requirements and use cases](docs/requirements/functional-requirements.md) | Required system behaviour, priorities, acceptance criteria and use cases. |
| [User persona](docs/requirements/user-persona.md)                                     | The intended user's goals, tasks and working environment.                 |
| [Hardware parts list](docs/hardware/hardware-parts-list.md)                           | Prototype components, their purpose and estimated costs.                  |
| [Sensor research](docs/research/sensor-research.md)                                   | Monitoring context, sensor comparison and proposed temperature logic.     |
| [Database research](docs/research/database-research.md)                               | Storage options, the proposed database choice and example schema.         |
| [Project schedule](docs/project/project-schedule.md)                                  | Sprint activities, deliverables and assessment milestones.                |

## Licence

This project is distributed under the [MIT licence](LICENSE).
