# TempSafe - MoSCoW Feature Prioritisation

Feature status was checked against `master` on **8 November 2026**. Of the 15 features, 4 are complete, 9 are in
progress and 2 are planned. Priorities are unchanged; FR-13 remains the only recorded priority change.
See the [functional requirements](functional-requirements.md) for the acceptance criteria.

## Feature priority matrix

✓ marks the current priority. In the FR-13 row, ← points from its former priority to its current one.
Items without an FR ID are follow-up ideas or exclusions. Implementation status is recorded in the sections below.

| ID    | Feature                                                                              | Must Have | Should Have | Could Have | Won’t Have This Time |
|-------|--------------------------------------------------------------------------------------|:---------:|:-----------:|:----------:|:--------------------:|
| FR-01 | Sign in and sign out                                                                 |    ✓     |             |            |                      |
| FR-02 | Restrict access to the assigned prototype box                                        |    ✓     |             |            |                      |
| FR-03 | Measure and record internal temperature                                              |    ✓     |             |            |                      |
| FR-04 | Show the latest temperature and its freshness                                        |    ✓     |             |            |                      |
| FR-05 | Classify readings against a configured profile                                       |    ✓     |             |            |                      |
| FR-06 | Provide a local LED warning                                                          |    ✓     |             |            |                      |
| FR-07 | Display temperature history                                                          |    ✓     |             |            |                      |
| FR-08 | Identify loss of device contact                                                      |    ✓     |             |            |                      |
| FR-09 | Buffer readings while offline                                                        |    ✓     |             |            |                      |
| FR-10 | Handle duplicate and delayed uploads                                                 |    ✓     |             |            |                      |
| FR-11 | Refresh the dashboard automatically                                                  |           |     ✓      |            |                      |
| FR-12 | Record review of a flagged sample                                                    |           |     ✓      |            |                      |
| FR-13 | Estimate observed excursion periods                                                  |    ✓     |      ←      |            |                      |
| FR-14 | Send phone notifications                                                             |    ✓     |             |            |                      |
| FR-15 | Provide an audible buzzer alert                                                      |           |     ✓      |            |                      |
| —     | Native mobile application                                                            |           |             |     ✓     |                      |
| —     | Automatic cooling or temperature regulation                                          |           |             |            |          ✓          |
| —     | GPS tracking and box-opening detection                                               |           |             |            |          ✓          |
| —     | Humidity, weight measurement and a second sensor for external-temperature comparison |           |             |            |          ✓          |
| —     | Integration with ambulance-service systems or ePCR                                   |           |             |            |          ✓          |
| —     | Patient records, medication administration and controlled-drug accounting            |           |             |            |          ✓          |
| —     | Automated clinical decisions about medicine use or disposal                          |           |             |            |          ✓          |
| —     | Clinical deployment or testing with real medicines                                   |           |             |            |          ✓          |

## What the implementation review found

- **FR-01.** Sign-in and sign-out are integrated and deployed. Failed logout now stays on the page
  with an error; only a 204 response shows the signed-out confirmation. See the
  [sign-in report](../testing/web/sign-in-test-report.md) and [authentication tests](../../tests/backend/test_auth.py).
- **FR-02.** The API enforces box assignments, including multiple users sharing a box. An unassigned
  user receives no readings, but the dashboard still shows a generic loading error rather than the
  intended no-access explanation. That interface work remains outstanding.
- **FR-03.** The Pi records temperatures and sensor errors in SQLite, but flags every timestamp as reliable.
  An unsynchronised clock can therefore produce a misleading observation time.
  See the [device logger](../../device/temperature_readings.py).
- **FR-04, FR-07 and FR-08.** The dashboard shows the age of a reading. Separate device contact and its timeout
  are still in progress. History shows a graph and table for the last 100 samples, with a time-range filter and
  historical limits still outstanding. See the [dashboard](../../frontend/js/dashboard.js) and
  [history view](../../frontend/js/history.js).
- **FR-06, FR-09 and FR-15.** The LED and buzzer respond locally. Deliberate network-loss testing and a manual
  buzzer silence control remain open. The SQLite queue retains unacknowledged readings, with the 24-hour outage,
  restart and upload check still outstanding. See the [LED test](../testing/hardware/led-patterns.md),
  [buzzer test](../testing/hardware/buzzer-alert.md) and [device queue](../../device/mqtt_publisher.py).
- **FR-13.** History shows an estimated duration and peak. With a 30-second sampling interval, high readings
  numbered 1 and 3 are joined when reading 2 is missing. If a delayed, in-range reading 2 arrives, reloading
  History splits the event in two. The missing observation should already break the period on the first view.
  See the [period calculation](../../frontend/js/history.js).
- **FR-12 and FR-14.** The schema provides a review table. Recording a review from the application and delivering
  phone notifications are still planned.

## Decision rules

- **Must Have:** without this feature, the core monitoring journey is incomplete or gives misleading information.
- **Should Have:** valuable for the user, but the core journey has an acceptable temporary alternative.
- **Could Have:** an enhancement to consider after the essential features are implemented and tested.
- **Won't Have This Time:** excluded from this release to keep the prototype achievable.

## Universal Design justification

The selected principles are documented in [design principles](../design/accessibility/design-principles.md):

- **P3 - Simple and Intuitive Use:** keep the main journey clear and reduce unnecessary interaction.
- **P4 - Perceptible Information:** communicate status through readable text, symbols and colour; distinguish current,
  stale and missing information.
- **P5 - Tolerance for Error:** make faults visible and prevent loss, duplication or misleading interpretation of
  records.

Accessibility is part of the essential interface, rather than an optional feature. Keyboard access, clear labels,
readable contrast, warnings that do not rely on colour alone and a table alternative to the graph apply to the Must Have
screens. Security and storage features also have technical justifications; their priority does not depend solely on
Universal Design.

## Must Have

| ID    | Feature                                        | Status      | Why it is essential                                                                                                                                                       | UX / Universal Design justification                                                                                                                                                                                  |
|-------|------------------------------------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01 | Sign in and sign out                           | Done        | Establish an authorised user session before accessing box data.                                                                                                           | P3: clear login, failure and logout states support a predictable journey.                                                                                                                                            |
| FR-02 | Restrict access to the assigned prototype box  | In progress | Multiple assigned users share the single prototype box; unassigned users are denied through both the interface and API.                                                   | P3/P5: a clear shared-box identity reduces confusion; permission enforcement prevents inappropriate access.                                                                                                          |
| FR-03 | Measure and record internal temperature        | In progress | Temperature monitoring is the purpose of the prototype; readings need identity, time and quality information.                                                             | P5: a failed sensor read must not become a plausible temperature value.                                                                                                                                              |
| FR-04 | Show the latest temperature and its freshness  | In progress | A value without its age can mislead the user about the current condition.                                                                                                 | P3/P4: show value, units, observation time and explicit unknown, stale or sensor-error states.                                                                                                                       |
| FR-05 | Classify readings against a configured profile | Done        | Users need to distinguish Normal, early Warning and Alert against the configured profile.                                                                                 | P4/P5: use named states and symbols; an invalid reading must never be labelled normal.                                                                                                                               |
| FR-06 | Provide a local LED warning                    | In progress | Local feedback must continue when the network is unavailable.                                                                                                             | P4/P5: use a single-colour LED on for Warning/Alert and a distinct blink pattern for sensor failure; the dashboard also uses text and symbols. An unlit LED is not proof of working power or acceptable temperature. |
| FR-07 | Display temperature history                    | In progress | A current reading cannot explain what happened earlier.                                                                                                                   | P4/P5: provide a graph and readable table, with visible gaps and original observation times.                                                                                                                         |
| FR-08 | Identify loss of device contact                | In progress | The user must be able to distinguish missing communication from valid current monitoring.                                                                                 | P4/P5: explicitly show not-reporting and never-connected states and last contact time.                                                                                                                               |
| FR-09 | Buffer readings while offline                  | In progress | Intermittent connectivity must not immediately erase observation history.                                                                                                 | P5: retain at least 24 hours of sample attempts through a normal restart; show limitations rather than implying uninterrupted monitoring.                                                                            |
| FR-10 | Handle duplicate and delayed uploads           | Done        | Reconnection must not duplicate records or replace the current state with older data.                                                                                     | P5: preserve trustworthy history and avoid presenting a delayed historical warning as a current event.                                                                                                               |
| FR-13 | Estimate observed excursion periods            | In progress | Moved from Should Have to Must Have because Shannon needs to see the estimated duration and peak temperature at a glance in the [main use case](main-use-case.md) (P3).   | P5: label durations as estimates and break periods at gaps in the readings.                                                                                                                                          |
| FR-14 | Send phone notifications                       | Planned     | Staff away from the box need a remote Warning or Alert with connectivity and permission. Define and test the delivery channel, recipients and repeated-state suppression. | P4/P5: clear box identity, reading and time; avoid misleading delayed alerts and expose delivery failures.                                                                                                           |

Early Warning is part of FR-05 and FR-06, not an optional enhancement. The physical LED does not distinguish states by
colour; the application uses green, amber and red with labels and symbols.

## Should Have

| ID    | Feature                             | Status      | Why it is valuable                                              | Temporary alternative and UD justification                                                                                                                     |
|-------|-------------------------------------|-------------|-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-11 | Refresh the dashboard automatically | Done        | Reduce repeated interaction while viewing status.               | A clearly labelled manual refresh can support the baseline journey. P3: automatic refresh reduces effort, with refresh failures visible.                       |
| FR-12 | Record review of a flagged sample   | Planned     | Help users record that a flagged observation has been reviewed. | The user can inspect history without recording acknowledgement. P3/P5: distinguish reviewed from resolved; acknowledgement must not remove an ongoing warning. |
| FR-15 | Provide an audible buzzer alert     | In progress | Add local audible feedback on Alert when available.             | P4: complement LED and application information. Visual feedback remains the temporary alternative; a silence control must not clear the warning.               |

## Could Have

A native mobile application is a possible follow-up, subject to team agreement. See the
[platform scope](../project-scope.md#application-platform) for the web application and planned PWA.

## Won't Have This Time

| Feature                                                                              | Reason for exclusion                                                                            |
|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| Automatic cooling or temperature regulation                                          | Monitoring is the core goal; active regulation introduces additional hardware and control work. |
| GPS tracking and box-opening detection                                               | These do not support the selected temperature-monitoring journey directly.                      |
| Humidity, weight measurement and a second sensor for external-temperature comparison | Separate research scope; one internal sensor is sufficient for the proposed baseline.           |
| Integration with ambulance-service systems or ePCR                                   | Requires external access and integration beyond the bench prototype.                            |
| Patient records, medication administration and controlled-drug accounting            | Outside the agreed monitoring scope.                                                            |
| Automated clinical decisions about medicine use or disposal                          | The prototype reports observations; staff follow their service's procedures.                    |
| Clinical deployment or testing with real medicines                                   | The assessed prototype is limited to demonstration and bench testing.                           |

## Confirmed direction and remaining implementation choices

- One internal temperature sensor and one single-colour LED; no RGB LED promise.
- Phone notifications are Must Have. Validate the proposed Web Push channel, browser support and permission handling
  before implementation
  is considered complete.
- The buzzer remains Should Have. A passive buzzer and its sound pattern have been tested; manual silencing remains
  outstanding. See the [buzzer test](../testing/hardware/buzzer-alert.md).
- Humidity and CO₂ reporting are outside this release, even though the SCD-41 can measure both.
- The agreed demo profile uses a 0.00°C lower threshold, 24.00°C warning threshold and 25.00°C upper limit.
  Alert applies at or below 0°C and above 25°C; Warning applies from 24°C through 25°C. These are prototype settings,
  not a universal medicine storage range.
- Record the clarified priorities and any subsequent group decisions in Scrumwise. This document does not claim that a
  group meeting or approval has occurred.
