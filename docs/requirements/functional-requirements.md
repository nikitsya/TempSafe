# Smart Box — Functional Requirements and Use Cases

**Date:** 8 October 2026 **Version:** 0.3 **Status:** Agreed project direction

Priority reasons, Universal Design links and proposed scope decisions are documented in
the [MoSCoW prioritisation](moscow-prioritisation.md). The hardware and notification priorities reflect the clarified
project direction.

## 1. Users and context (UTSE)

| Element      | Proposed definition                                                                                                                                       |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Users        | Paramedic or staff member authorised to monitor assigned boxes; exact operational responsibility to be validated                                          |
| Tasks        | Check temperature and data freshness, inspect out-of-range observations, review history and acknowledge review                                            |
| Systems      | One temperature sensor, Raspberry Pi, local SQLite queue, authenticated HTTPS API, MySQL database and web application                                     |
| Environments | Portable medication box used in an emergency-service context; initial demonstration on a bench with no medicines; intermittent Wi-Fi/hotspot connectivity |

## 3. Functional requirements

| ID    | Requirement                                          | Priority | Acceptance criteria                                                                                                                                                                                                                                                                                            |
|-------|------------------------------------------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01 | Sign in and sign out                                 | Must     | Valid credentials grant a session; invalid credentials do not; sign-out invalidates the session                                                                                                                                                                                                                |
| FR-02 | Restrict access to assigned boxes                    | Must     | Both UI and API enforce box permissions; changing a box ID does not expose another user's data                                                                                                                                                                                                                 |
| FR-03 | Measure and record internal temperature              | Must     | Each sample attempt has a unique ID, box ID, persistent sequence number, UTC observation time (or explicit unreliable-clock status), profile ID and quality status; valid readings are recorded in degrees Celsius                                                                                             |
| FR-04 | Show the latest temperature and its freshness        | Must     | Show value, unit, observation time and last device contact separately; show unknown before any reading and stale when readings are old; a newer sensor error is visible even if the last valid value remains in history                                                                                        |
| FR-05 | Classify valid samples against a configured profile  | Must     | With limits L < W < U: T < L or T > U is Alert; W <= T <= U is Warning; L <= T < W is Normal. W is the configured early-warning threshold; invalid samples are unknown, never Normal; preserve the applied profile                                                                                             |
| FR-06 | Provide a local LED warning                          | Must     | A single-colour LED lights by the next completed Warning or Alert sample, including without Wi-Fi; Normal turns it off; an invalid read uses a distinct blink pattern; off is not proof of acceptable conditions or working power                                                                              |
| FR-07 | Display temperature history and out-of-range records | Must     | Filter by box and time; provide graph plus readable table; show thresholds, gaps and quality issues; use observation times, not upload times                                                                                                                                                                   |
| FR-08 | Identify loss of device contact                      | Must     | After the contact timeout show not reporting and the last contact time; never-connected devices have a separate state; contact alone does not make buffered readings fresh                                                                                                                                     |
| FR-09 | Buffer data while offline                            | Must     | At least 24 hours at the configured sampling interval survive a normal device restart and upload after reconnection; original IDs and times are retained; unacknowledged records are not discarded                                                                                                             |
| FR-10 | Handle duplicate and delayed uploads                 | Must     | Identical retries create one sample; conflicting reuse of an ID is rejected; old data does not replace the latest state or trigger a misleading current warning                                                                                                                                                |
| FR-11 | Refresh the dashboard automatically                  | Should   | With connectivity, accepted data appears within the proposed five-second polling interval; refresh failure is visible                                                                                                                                                                                          |
| FR-12 | Record that a user has reviewed a flagged sample     | Should   | Store reviewer and server timestamp for a flagged sample; acknowledgement does not change the measurement or remove an ongoing warning                                                                                                                                                                         |
| FR-13 | Estimate observed excursion periods                  | Should   | Group consecutive low/high observations using observation order; label duration as estimated; missing/invalid samples break continuity; delayed data causes affected history to be recalculated                                                                                                                |
| FR-14 | Send phone notifications                             | Must     | With connectivity and notification permission, send a clear Warning or Alert notification to authorised recipients; define and test the phone delivery channel, suppress repeated notifications for an unchanged state, distinguish delayed historical events from current alerts and expose delivery failures |
| FR-15 | Provide an audible buzzer alert                      | Should   | If implemented, sound on Alert, operate locally without Wi-Fi and provide a silence control; silencing does not clear the LED or dashboard state. Define and test the sound pattern and repeat behaviour.                                                                                                      |

## 4. Proposed prototype settings

For the existing demo profile, the early-warning threshold is 24°C and the upper limit is 25°C; the lower limit remains
to be selected. Boundary tests cover L, W and U, including exact equality. These settings do not define a universal
medicine storage range.

| Setting            | Proposal                                                                                                                                              |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sampling interval  | 30 seconds                                                                                                                                            |
| Heartbeat interval | 60 seconds; transmitted independently of whether the sensor read succeeds                                                                             |
| Contact timeout    | 3 minutes                                                                                                                                             |
| Local buffer       | At least 24 hours (2,880 sample attempts at 30-second intervals)                                                                                      |
| Threshold profile  | Immutable versioned lower/upper limits, early-warning threshold and source note; configured by the team, not hard-coded as a universal medicine range |

## 5. Use cases

### UC-01 — Sign in and select a box

**Actor:** Authorised user. **Requirements:** FR-01, FR-02.

1. User signs in and sees assigned boxes.
2. User selects a box.
3. Backend checks permissions on every request.

Invalid credentials, an empty assignment list and denied access have explicit UI states.

### UC-02 — Record a sample and provide a local warning

**Actor:** Device. **Requirements:** FR-03, FR-05, FR-06, FR-09, FR-10.

1. Read the internal sensor every 30 seconds.
2. Record a valid temperature or a sensor-error status; never substitute zero for failure.
3. Compare a valid value with the provisioned profile and update the local LED.
4. Persist the sample and transmit it if connectivity is available.
5. Server authenticates the device, validates its box/profile, and stores the sample idempotently.

A read failure or unsynchronised clock is identified explicitly. A network failure does not stop local sampling or the
LED. Loss of electrical power stops the prototype; it is not a fail-safe medical alarm.

### UC-03 — Check current condition

**Actor:** Authorised user. **Requirements:** FR-02, FR-04, FR-05, FR-08, FR-11.

1. Open dashboard and check temperature, profile limits and timestamps.
2. View Normal (green), Warning (amber) or Alert (red), with text and symbols as well as colour; show sensor-error and
   stale states separately.
3. Distinguish a currently received warning from a historical event uploaded late.

No measurements means unknown. A connected device with failed reads is not shown as healthy temperature monitoring.

### UC-04 — Review history and flagged observations

**Actor:** Authorised user. **Requirements:** FR-02, FR-07, FR-12, FR-13.

1. Select a time interval and inspect temperature graph and table.
2. Review out-of-range observations with their original profile.
3. If implemented, view estimated excursion periods and record acknowledgement.

Empty and invalid intervals have explanatory states. Gaps are not drawn as proof of continuous safe conditions.

### UC-05 — Recover from a network outage

**Actor:** Device. **Requirements:** FR-08, FR-09, FR-10.

1. Continue sampling, local warnings and durable queuing offline.
2. Reconnect and transmit records with unchanged IDs, sequence numbers and times.
3. Delete/mark queue entries delivered only after acknowledgement.
4. Show restored contact, while showing the actual age of the latest reading.

A lost acknowledgement causes a safe retry. Records older than the latest sample enrich history without rolling current
status back. Exceeding tested capacity or loss of power is reported as a limitation.

### UC-06 — Receive a phone notification

**Actor:** Authorised user. **Requirements:** FR-05, FR-14.

1. Enable notifications through the selected phone delivery channel.
2. Receive a Warning or Alert notification containing the box identity, temperature and observation time when
   connectivity is available.
3. Open the application to check current freshness and history.

Repeated unchanged states must not flood the phone. Denied permission, missing connectivity and delivery failures must
be tested. Phone delivery is not guaranteed during an outage; local LED feedback continues.

## 6. Traceability and testing

| Use case | Requirements                      | Planned evidence                                                                                              |
|----------|-----------------------------------|---------------------------------------------------------------------------------------------------------------|
| UC-01    | FR-01, FR-02                      | Valid/invalid login, logout and denied cross-box API access                                                   |
| UC-02    | FR-03, FR-05, FR-06, FR-09, FR-10 | Reference thermometer comparison; synthetic boundary values; disconnected sensor; local LED during Wi-Fi loss |
| UC-03    | FR-02, FR-04, FR-05, FR-08, FR-11 | Fresh, stale, never-connected and read-failure UI demonstrations                                              |
| UC-04    | FR-02, FR-07, FR-12, FR-13        | Filtered history, visible gaps, acknowledgement and delayed-event recalculation                               |
| UC-05    | FR-08, FR-09, FR-10               | Recorded outage/restart, queue reconciliation and duplicate resend                                            |
| UC-06    | FR-05, FR-14                      | Phone receipt, permission denial, repeated-state suppression, delivery failure and delayed-upload scenarios   |

Buzzer testing (FR-15), if implemented: local activation on Alert, operation without Wi-Fi and silencing without
clearing the warning.

## 7. UX and boundaries

- Keyboard-accessible controls, readable labels, Celsius units and accessible table alternative to charts.
- Clear observation and receipt times; no colour-only warnings.
- No patient records, prescribing, drug-dose accounting or automated medicine-disposal decisions.
- One internal temperature sensor only; humidity, weight, external-temperature and opening measurements are outside this
  release.
- The physical LED is a single-colour output device; application status colours do not require an RGB LED.
