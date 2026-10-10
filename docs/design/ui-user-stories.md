# UI user stories

Author: Maryna Hordiienko

The design document (Section 1) has four main user stories. This file adds detailed UI stories for the persona Shannon Rice ([user-persona.md](../requirements/user-persona.md)). Each story is linked to a functional requirement in [functional-requirements.md](../requirements/functional-requirements.md) and uses the same MoSCoW priority, so no new features are added here.

| ID | User story | Acceptance criteria | Requirement | Priority |
|---|---|---|---|---|
| US-UI-01 | As a paramedic, I want to sign in with my email and password so that only I can see my assigned box. | Labelled fields; generic error on failure; session ends on sign-out. | FR-01 | Must |
| US-UI-02 | As a paramedic, I want to see the status at a glance so that I do not need to read numbers during a call. | Status heading, symbol and colour are visible without scrolling on a phone. | FR-04, FR-05 | Must |
| US-UI-03 | As a paramedic, I want to know how old the reading is so that I do not trust old data. | Observation time and age shown; Data stale after 90 s. | FR-04 | Must |
| US-UI-04 | As a paramedic, I want a clear message when the sensor fails so that I know the temperature is unknown. | Sensor error state; failed reading never shown as 0°C or Normal. | FR-04 | Must |
| US-UI-05 | As a paramedic, I want to know when the device stops reporting so that I can check its power and connection. | Not reporting state after 180 s with last contact time. | FR-08 | Must |
| US-UI-06 | As a paramedic, I want to see past temperatures for a time range so that I can check what happened during a shift. | From/To filter, graph and table, gaps shown. | FR-07 | Must |
| US-UI-07 | As a paramedic, I want phone notifications for Warning and Alert so that I do not need to keep the app open. | Web Push after permission; banner if denied or unsupported. | FR-14 | Must |
| US-UI-08 | As a user without an assigned box, I want a clear message so that I know to ask for access. | No assigned box message; no other box data visible. | FR-02 | Must |
| US-UI-09 | As a paramedic who uses only the keyboard or a screen reader, I want every feature to be accessible so that I can use the app without a mouse. | Criteria AC-03 to AC-07 in [accessibility-criteria.md](accessibility-criteria.md) pass. | FR-07, Principle 4 | Must |
| US-UI-10 | As a paramedic, I want the dashboard to update by itself so that I do not need to reload the page. | New accepted data appears within about 5 s while online. | FR-11 | Should |
