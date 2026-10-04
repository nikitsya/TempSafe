# Smart Box — Functional Requirements and Use Cases

**Date:** 4 October 2026  
**Version:** 0.2  
**Status:** Agreed project direction

## 1. Users and context (UTSE)

| Element      | Proposed definition                                                                                                                                       |
|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Users        | Paramedic or staff member authorised to monitor assigned boxes; exact operational responsibility to be validated                                          |
| Tasks        | Check temperature and data freshness, inspect out-of-range observations, review history and acknowledge review                                            |
| Systems      | One temperature sensor, Raspberry Pi, local SQLite queue, authenticated HTTPS API, MySQL database and web application                                     |
| Environments | Portable medication box used in an emergency-service context; initial demonstration on a bench with no medicines; intermittent Wi-Fi/hotspot connectivity |

## 3. Functional requirements

| ID    | Requirement                                              | Priority | Acceptance criteria                                                                                                                                                                                                     |
|-------|----------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01 | Sign in and sign out                                     | Must     | Valid credentials grant a session; invalid credentials do not; sign-out invalidates the session                                                                                                                         |
| FR-02 | Restrict access to assigned boxes                        | Must     | Both UI and API enforce box permissions; changing a box ID does not expose another user's data                                                                                                                          |
| FR-03 | Measure and record internal temperature                  | Must     | Each sample attempt has a unique ID, box ID, persistent sequence number, UTC observation time (or explicit unreliable-clock status), profile ID and quality status; valid readings are recorded in degrees Celsius      |
| FR-04 | Show the latest temperature and its freshness            | Must     | Show value, unit, observation time and last device contact separately; show unknown before any reading and stale when readings are old; a newer sensor error is visible even if the last valid value remains in history |
| FR-05 | Classify valid samples against a configured profile      | Must     | With limits L < U: T < L is low, T > U is high, and L <= T <= U is within range; invalid samples are unknown, never normal; the applied profile is preserved                                                            |
| FR-06 | Warn locally when valid readings are outside the profile | Must     | A dedicated warning LED turns on by the next completed out-of-range sample, including without Wi-Fi; an invalid read uses a distinct blink pattern; off is not proof of safe conditions or working power                |
| FR-07 | Display temperature history and out-of-range records     | Must     | Filter by box and time; provide graph plus readable table; show thresholds, gaps and quality issues; use observation times, not upload times                                                                            |
| FR-08 | Identify loss of device contact                          | Must     | After the contact timeout show not reporting and the last contact time; never-connected devices have a separate state; contact alone does not make buffered readings fresh                                              |
| FR-09 | Buffer data while offline                                | Must     | At least 24 hours at the configured sampling interval survive a normal device restart and upload after reconnection; original IDs and times are retained; unacknowledged records are not discarded                      |
| FR-10 | Handle duplicate and delayed uploads                     | Must     | Identical retries create one sample; conflicting reuse of an ID is rejected; old data does not replace the latest state or trigger a misleading current warning                                                         |
| FR-11 | Refresh the dashboard automatically                      | Should   | With connectivity, accepted data appears within the proposed five-second polling interval; refresh failure is visible                                                                                                   |
| FR-12 | Record that a user has reviewed a flagged sample         | Should   | Store reviewer and server timestamp for a flagged sample; acknowledgement does not change the measurement or remove an ongoing warning                                                                                  |
| FR-13 | Estimate observed excursion periods                      | Should   | Group consecutive low/high observations using observation order; label duration as estimated; missing/invalid samples break continuity; delayed data causes affected history to be recalculated                         |
| FR-14 | Send email/push notifications                            | Could    | Only after a delivery channel, recipient permissions and deduplication rules are defined; not part of baseline promises                                                                                                 |

## 4. Proposed prototype settings

| Setting            | Proposal                                                                                                                     |
|--------------------|------------------------------------------------------------------------------------------------------------------------------|
| Sampling interval  | 30 seconds                                                                                                                   |
| Heartbeat interval | 60 seconds; transmitted independently of whether the sensor read succeeds                                                    |
| Contact timeout    | 3 minutes                                                                                                                    |
| Local buffer       | At least 24 hours (2,880 sample attempts at 30-second intervals)                                                             |
| Threshold profile  | Immutable versioned lower/upper limits and source note; configured by the team, not hard-coded as a universal medicine range |

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
2. View within range / low / high / sensor error / stale status using text and symbols, not colour alone.
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

## 6. Traceability and testing

| Use case | Requirements                      | Planned evidence                                                                                              |
|----------|-----------------------------------|---------------------------------------------------------------------------------------------------------------|
| UC-01    | FR-01, FR-02                      | Valid/invalid login, logout and denied cross-box API access                                                   |
| UC-02    | FR-03, FR-05, FR-06, FR-09, FR-10 | Reference thermometer comparison; synthetic boundary values; disconnected sensor; local LED during Wi-Fi loss |
| UC-03    | FR-02, FR-04, FR-05, FR-08, FR-11 | Fresh, stale, never-connected and read-failure UI demonstrations                                              |
| UC-04    | FR-02, FR-07, FR-12, FR-13        | Filtered history, visible gaps, acknowledgement and delayed-event recalculation                               |
| UC-05    | FR-08, FR-09, FR-10               | Recorded outage/restart, queue reconciliation and duplicate resend                                            |

## 7. UX and boundaries

- Keyboard-accessible controls, readable labels, Celsius units and accessible table alternative to charts.
- Clear observation and receipt times; no colour-only warnings.
- No patient records, prescribing, drug-dose accounting or automated medicine-disposal decisions.
- Future external temperature comparison is separate research scope, not a second sensor promised for this release.
