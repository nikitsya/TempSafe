# Smart Box

**Class Group:** SD3a-G2  
**Team Size:** 3 members

**Documentation last updated:** 4 October 2026

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

Smart Box monitors the temperature inside the box, keeps a history of readings and warns when a reading falls outside
the configured range. Staff can check the latest information and review earlier changes.

For example, if the temperature rises above the set limit during a shift, the system highlights the change. The
responsible person can check the box and follow their service's procedures. The recorded history remains available for
later review.

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