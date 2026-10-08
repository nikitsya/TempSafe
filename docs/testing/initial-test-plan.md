# Smart Box / TempSafe - Initial Test Plan

**Date:** 8 October 2026

## Purpose

Plan how to verify the [functional requirements](../requirements/functional-requirements.md) and
selected [Universal Design principles](../design/design-principles.md). This document describes future testing.

## Equipment and prerequisites

- Raspberry Pi 400, Adafruit SCD-41, single-colour LED, suitable resistor, wiring and power supply; prototype box.
- Reference thermometer for comparison; record its stated accuracy and placement.
- Device software, local SQLite queue, backend, MySQL and web application when available.
- Controllable Wi-Fi, a phone with the chosen notification channel and two authorised users assigned to the same
  physical prototype box, plus an unassigned test user.
- Synthetic readings and controlled faults for repeatable boundary/recovery tests; these do not prove physical sensor
  accuracy.
- Browser developer tools, keyboard, contrast checker and a screen reader.
- Buzzer and silence control only if implemented. Power off the circuit before changing wiring.

## Settings to record before execution

| Setting                  | Proposal or required decision                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------------------------------------|
| Sampling interval        | 30 seconds                                                                                                         |
| Heartbeat interval       | 60 seconds                                                                                                         |
| Device-contact timeout   | 3 minutes                                                                                                          |
| Offline capacity         | At least 24 hours: 2,880 attempts at 30-second intervals                                                           |
| Profile                  | L < W < U. Demo W = 24°C; U = 25°C. Lower limit L remains to be agreed.                                            |
| Stale-reading threshold  | Agree separately from device-contact timeout.                                                                      |
| Measurement tolerance    | Agree from sensor and reference specifications before physical comparison.                                         |
| Notifications            | Select channel; agree recipients, repeat suppression, delivery-time target, failure indication and recovery rules. |
| LED sensor-error pattern | Define a blink pattern distinguishable from a steady warning.                                                      |
| Buzzer, if implemented   | Define sound pattern, repetition, silence and reset behaviour.                                                     |

## Functional tests

Each case specifies preconditions, actions and expected outcomes. All cases are initially **Not Run**; collect actual
results separately.

| ID / requirements           | Preconditions                                                  | Actions                                                                                                                                                                         | Expected result                                                                                                                                                                                    |
|-----------------------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TP-01 / FR-01               | User exists; backend reachable.                                | Sign in correctly; sign out; reuse the old session against a protected endpoint.                                                                                                | Access is granted initially; sign-out invalidates the session and further access is denied.                                                                                                        |
| TP-02 / FR-01               | Login available.                                               | Submit wrong credentials and empty fields.                                                                                                                                      | No session is granted; clear errors appear without exposing credentials.                                                                                                                           |
| TP-03 / FR-02               | One physical box; users A/B assigned to it; user C unassigned. | As A/B, open the shared box; as C, request its data through the UI and API; try a non-existent box ID.                                                                          | A/B can access the same box; C is denied in both UI and API with a clear no-access state; unknown IDs expose no data. No second physical box is required.                                          |
| TP-04 / FR-03               | Sensor/reference placed together; tolerance agreed.            | Compare stable readings under several controlled conditions in the assembled box; assess placement, self-heating and any configured temperature offset; inspect stored records. | Differences meet agreed tolerance; each record has value/unit, ID, box, sequence, time, profile and quality. Record discrepancies.                                                                 |
| TP-05 / FR-03               | Sampling configured.                                           | Observe multiple attempts; restart normally; inspect subsequent records.                                                                                                        | Attempts follow the interval; IDs remain unique and persistent sequence numbers do not cause conflicts after restart.                                                                              |
| TP-06 / FR-05               | Synthetic input and spaced L/W/U limits available.             | Inject each value in the boundary table below, plus invalid data.                                                                                                               | Classification matches the table, including equality; invalid values are never Normal.                                                                                                             |
| TP-07 / FR-05               | Versioned profiles supported.                                  | Record data, change profile, record again and inspect history; attempt L >= W or W >= U.                                                                                        | Original interpretation remains attached to older observations; invalid profile ordering is rejected.                                                                                              |
| TP-08 / FR-06               | Single-colour LED connected.                                   | Inject Normal, Warning, Alert and Normal in order.                                                                                                                              | LED is off, on, on and off by the next completed sample; no physical colour change is expected.                                                                                                    |
| TP-09 / FR-03–FR-06         | Previously valid Normal and Alert readings available.          | Simulate sensor failure in each state; inspect records, LED and dashboard.                                                                                                      | Error quality and distinct blinking appear; error is not replaced by zero or Normal; previous valid readings are clearly historical.                                                               |
| TP-10 / FR-03, FR-04        | Clock failure can be simulated.                                | Record with an unreliable clock; inspect display/history.                                                                                                                       | Clock unreliability is explicit and the reading is not presented as reliably timed fresh data.                                                                                                     |
| TP-11 / FR-04, FR-08        | Freshness threshold agreed.                                    | Inspect a box without readings; send data; stop samples but continue heartbeats beyond freshness threshold.                                                                     | Unknown initially; value/unit, observation and contact times shown separately; contact does not refresh old data.                                                                                  |
| TP-12 / FR-08               | One previously connected and one never-connected device.       | Stop contact for more than 3 minutes; restore it.                                                                                                                               | Not-reporting state and last contact shown; never-connected state distinct; reconnection does not falsely refresh buffered readings.                                                               |
| TP-13 / FR-07               | History includes all states, gaps and errors.                  | Filter by box/time; compare graph/table; try empty/invalid intervals.                                                                                                           | Correct records, original times and thresholds appear; gaps/quality issues visible; empty/invalid states explained.                                                                                |
| TP-14 / FR-06, FR-09        | Device powered; Wi-Fi controllable.                            | Disconnect Wi-Fi; generate Warning and Alert; inspect LED/queue.                                                                                                                | Local sampling, LED and durable queuing continue; phone delivery is not assumed offline.                                                                                                           |
| TP-15 / FR-09, FR-10        | Offline capacity environment prepared.                         | Run offline for 24 hours at 30-second intervals, including a normal restart; reconnect and reconcile IDs/counts.                                                                | At least 2,880 attempts supported; queued records survive restart, upload with original IDs/times and show no unexplained loss or duplicates. Accelerated tests supplement the real-duration test. |
| TP-16 / FR-09, FR-10        | Acknowledgement loss can be simulated.                         | Store an upload but lose acknowledgement; retry identical records; reuse an ID with different content.                                                                          | Identical retry creates one record; conflicting reuse rejected; unacknowledged data retained.                                                                                                      |
| TP-17 / FR-04, FR-10, FR-14 | Newer Normal data current; older Alert data queued.            | Upload old records; inspect current state, history and phone.                                                                                                                   | History gains records without rolling back current state or sending a misleading current Alert.                                                                                                    |
| TP-18 / FR-14               | Channel chosen; authorised phone connected and permitted.      | Transition Normal → Warning → Alert; record receipt times; open notifications.                                                                                                  | Clear box identity, temperature/time delivered within agreed target; link opens correct authorised box.                                                                                            |
| TP-19 / FR-14               | Repeat rules defined.                                          | Send repeated unchanged warnings, then a genuine transition; inspect recipients.                                                                                                | No flood for unchanged states; transitions follow rules; unauthorised recipients receive no box data.                                                                                              |
| TP-20 / FR-14               | Permission/network/provider faults controllable.               | Deny permission, disconnect, simulate rejection and restore delivery.                                                                                                           | Failures exposed; no false success; LED continues; recovery follows agreed rules without duplicates or misleading old alerts.                                                                      |

### Boundary expectations for TP-06

| Input             | Expected state                        |
|-------------------|---------------------------------------|
| L−0.1             | Alert                                 |
| L, L+0.1          | Normal, provided L+0.1 < W            |
| W−0.1             | Normal, provided W−0.1 >= L           |
| W, W+0.1          | Warning, provided W+0.1 <= U          |
| U−0.1, U          | Warning, provided U−0.1 >= W          |
| U+0.1             | Alert                                 |
| Invalid / missing | Unknown or sensor error, never Normal |

## Conditional Should Have tests

| ID / requirements | Preconditions                      | Actions                                                                      | Expected result                                                                                                |
|-------------------|------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| TP-21 / FR-11     | Automatic refresh implemented.     | Upload new data without interacting; interrupt requests.                     | Dashboard updates within proposed five-second polling interval; refresh failures visible.                      |
| TP-22 / FR-12     | Acknowledgement implemented.       | Review a flagged observation; inspect reviewer/time, reading and warning.    | Reviewer/server time recorded; measurement unchanged; active warning not cleared.                              |
| TP-23 / FR-13     | Summaries implemented.             | Submit consecutive out-of-range data, errors, gaps and delayed observations. | Estimated summaries use observation order, break at gaps/errors and recalculate affected history.              |
| TP-24 / FR-15     | Buzzer implemented; rules defined. | Trigger Alert online/offline; silence; return to Normal; trigger again.      | Local sound follows rules; silence does not clear LED/dashboard; reset/repeat behaviour matches specification. |

## UX and Universal Design tests

| ID / principles and requirements       | Preconditions                         | Actions                                                                                                                       | Expected result                                                                                                       |
|----------------------------------------|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| UX-01 / P4; FR-04, FR-05, FR-08        | All status screens available.         | Hide colour/view greyscale; ask users to identify Normal, Warning, Alert, stale and sensor-error states.                      | Text/symbols communicate states independently of colour; incorrect interpretations recorded.                          |
| UX-02 / P4; FR-04, FR-07               | Contrast checker; phone viewport.     | Check contrast, 200% zoom, narrow viewport and bright/dim conditions.                                                         | Text meets project 4.5:1 contrast target; key values/controls remain readable without clipping; limitations recorded. |
| UX-03 / P3; FR-01, FR-02, FR-04, FR-07 | Task script ready.                    | Without coaching, ask users to sign in, open the shared assigned box, identify condition and find an earlier flagged reading. | Journey understandable; completion/time/errors recorded and improvements identified.                                  |
| UX-04 / P3/P4; FR-01, FR-02, FR-07     | Keyboard and screen reader available. | Navigate login, the shared box dashboard/history; read status and table with screen reader.                                   | Meaningful labels, visible focus, logical order and no keyboard traps; information accessible without graph.          |
| UX-05 / P5; FR-04, FR-08, FR-10        | Fault/stale/delayed scenarios ready.  | Ask users whether data is current and what is missing.                                                                        | Old, missing or invalid data distinguishable; misleading interpretations logged as defects.                           |
| UX-06 / P4/P5; FR-14                   | Test phone notifications available.   | Ask users to identify box, temperature/time and next step from Warning/Alert messages.                                        | Messages understandable; link leads to correct box; receipt does not imply a fresh reading.                           |

## Execution record and evidence

Use **Not Run**, **Blocked**, **Pass**, **Fail** or **Not Applicable**. Record reasons for Blocked/Not Applicable.
Evidence can include screenshots, paired thermometer readings, queue IDs/counts, API responses, notification timings and
participant notes.

| Test ID                             | Tester / date | Build / settings | Actual result | Status | Evidence / defect link |
|-------------------------------------|---------------|------------------|---------------|--------|------------------------|
| To be completed when testing begins | —             | —                | -             | -      | —                      |
