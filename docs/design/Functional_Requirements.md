# Smart Box — Functional Requirements and Use Cases

**Date:** 1 October 2026  
**Version:** 0.1  
**Status:** Draft for team review

## 1. Purpose

Smart Box is an IoT project intended to help paramedics monitor an equipment box. The proposed first version records lid
opening and closing, reports the box's location, and provides a web interface for viewing its latest reported state and
event history.

## 2. Scope and assumptions

### Proposed first version

- An authorised user signs in and accesses permitted boxes.
- The device detects whether the lid is open or closed.
- The system records lid transitions and valid location observations.
- The interface displays the latest reported lid state, last known location and observation timestamps.
- The user can review historical events.
- The interface indicates when the device has stopped reporting.

## 3. Actors

| Actor                       | Role                                                                                                               |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------|
| Paramedic / authorised user | Signs in, checks permitted boxes, views location and reviews history                                               |
| Smart Box device            | Detects lid changes and submits observations and contact updates                                                   |
| Project team                | Provisions the prototype's accounts, devices and access permissions; not a separate application role in this draft |

The backend, database and web interface are parts of the Smart Box system rather than separate end-user actors.

## 4. Priority definitions

| Priority                     | Meaning in this draft                                               |
|------------------------------|---------------------------------------------------------------------|
| Must have                    | Required for the proposed core prototype                            |
| Should have                  | Valuable resilience or usability feature, after the core flow works |
| Could have                   | Optional extension if time and hardware allow                       |
| Won't have in this iteration | Explicitly excluded from this proposed iteration                    |

## 5. Functional requirements

| ID    | Requirement                                                                                                                             | Priority    | Acceptance criteria                                                                                                                                                                                                 |
|-------|-----------------------------------------------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FR-01 | The system shall allow a provisioned user to sign in and sign out.                                                                      | Must have   | Valid credentials establish a session; invalid credentials do not. After sign-out, protected information cannot be retrieved using the ended session.                                                               |
| FR-02 | The system shall restrict each user's access to permitted boxes.                                                                        | Must have   | The user sees only permitted boxes. A direct request for an unpermitted box returns no box telemetry, even if its identifier is known.                                                                              |
| FR-03 | The system shall display the latest reported lid position for a selected box.                                                           | Must have   | The interface shows open or closed with its observation time. Before the first report it shows unknown. Old readings are labelled as stale rather than presented as live.                                           |
| FR-04 | The system shall record each detected, stable lid transition with its box identifier and observation time.                              | Must have   | One deliberate opening followed by one closing produces two transition records. Sensor bounce does not create extra transitions. A startup state snapshot is distinguishable from a new opening.                    |
| FR-05 | The system shall store valid location observations for the correct box.                                                                 | Must have   | Each stored observation identifies the box, coordinates and observation time. Invalid coordinates are rejected. An unavailable location fix is not replaced with invented coordinates.                              |
| FR-06 | The system shall show the selected box's last known location on a map.                                                                  | Must have   | A stored valid location is shown as a map marker with its observation time. If no location is available, the interface states this. If the map cannot load, coordinates and their timestamp remain available.       |
| FR-07 | The system shall allow the user to view lid-event history for a selected box and time interval.                                         | Must have   | The results contain only that permitted box's events in the requested interval, ordered by observation time. An empty interval displays an explanatory empty state.                                                 |
| FR-08 | The system shall indicate whether a box has recently contacted the server.                                                              | Must have   | After the configured contact timeout, the interface marks the device as not recently reporting and shows its last contact time. A valid new contact updates this status. A never-connected box is shown separately. |
| FR-09 | The device shall retain pending observations during a network interruption and upload them when connectivity returns.                   | Should have | During a controlled disconnection within the agreed buffer capacity, recorded events survive a normal device restart and are uploaded after reconnection. They retain their original observation times.             |
| FR-10 | The system shall process repeated and delayed uploads without duplicating events or replacing a newer reported state with an older one. | Must have   | Resending the same event produces one history entry. Uploading an older event after a newer event preserves both in history but does not roll back the latest state.                                                |
| FR-11 | The dashboard shall refresh box information without requiring the user to reload the entire page.                                       | Should have | While the dashboard is open and connected, newly accepted data appears within the agreed refresh interval. A failed refresh is indicated while previous readings retain their timestamps.                           |

### Proposed configuration for the prototype

| Setting                             | Proposed starting value                  | What needs confirmation                                 |
|-------------------------------------|------------------------------------------|---------------------------------------------------------|
| Location reporting interval         | 30 seconds when a valid fix is available | Receiver capability, power use and network availability |
| Device contact / heartbeat interval | 60 seconds                               | Battery and connectivity constraints                    |
| Device contact timeout              | 3 minutes                                | Appropriate tolerance for normal network interruptions  |
| Dashboard refresh interval          | 5 seconds                                | Backend load and acceptable user experience             |
| Offline buffer capacity             | To be agreed before FR-09 testing        | Expected outage duration and device storage             |
| Historical data retention           | To be agreed                             | How much history users need and available storage       |

## 6. Main use cases

### UC-01 — Sign in and access a box

**Primary actor:** Authorised user  
**Goal:** Access the monitoring information for a permitted box.  
**Preconditions:** The user has a provisioned account.  
**Trigger:** The user opens the application.  
**Requirements:** FR-01, FR-02

**Main flow:**

1. The application displays the sign-in screen.
2. The user enters their credentials.
3. The system validates the credentials and establishes a session.
4. The system displays the boxes available to that user.
5. The user selects a box and opens its dashboard.

**Alternative flows:**

- Invalid credentials: the system displays a sign-in error and does not provide protected data.
- No assigned boxes: the system displays an empty state explaining that no boxes are available to the user.
- Unauthorised box request: the system refuses access without returning its telemetry.

**Postcondition:** The user has an authenticated session and can access only permitted boxes.

### UC-02 — Check lid status

**Primary actor:** Authorised user  
**Goal:** Check the latest reported lid position.  
**Preconditions:** The user is signed in and has access to the box.  
**Trigger:** The user opens the box dashboard.  
**Requirements:** FR-02, FR-03, FR-08, FR-11

**Main flow:**

1. The user selects the box.
2. The system retrieves the latest lid observation and contact information.
3. The dashboard displays open or closed and the observation time.
4. While the dashboard remains open, it refreshes according to the agreed interval if FR-11 is included.

**Alternative flows:**

- No lid observation: display unknown, not closed by default.
- Device contact timeout: retain the last reported lid position and clearly indicate that it may be outdated.
- Refresh failure: show that the information could not be updated; do not change the observation timestamp.

**Postcondition:** The user can distinguish the latest reported lid position from an unknown or stale reading.

### UC-03 — Record an opening or closing

**Primary actor:** Smart Box device  
**Goal:** Preserve a reliable record of a physical lid transition.  
**Preconditions:** The device is provisioned and the lid sensor is configured.  
**Trigger:** The sensor detects a stable change in lid position.  
**Requirements:** FR-04, FR-09, FR-10

**Main flow:**

1. A person physically opens or closes the lid.
2. The device confirms the stable change and creates an observation with a unique identifier, box identifier, state and
   observation time.
3. If offline buffering is included, the device saves the pending observation locally before transmission.
4. The device sends the observation to the backend.
5. The backend authenticates the device and validates the observation.
6. The system stores the observation and acknowledges successful acceptance.
7. The observation becomes available in history and, if newer, updates the latest reported state.

**Alternative flows:**

- Network unavailable: if FR-09 is included, retain the observation and follow UC-06.
- Duplicate upload: acknowledge the already accepted matching observation without creating another history entry.
- Invalid observation or wrong device identity: reject it; do not update the box's state.
- Startup snapshot: record the observed state as an initial snapshot rather than a new opening or closing transition.

**Postcondition:** One valid transition is represented once in stored history after successful upload.

A lid sensor does not identify the person who opened the box. This use case must not claim to record a person's identity
without a separate identification mechanism.

### UC-04 — Locate a box

**Primary actor:** Authorised user  
**Goal:** Find the box's last known reported location.  
**Preconditions:** The user is signed in and has access to the box.  
**Trigger:** The user opens the location view.  
**Requirements:** FR-02, FR-05, FR-06, FR-08

**Main flow:**

1. The user selects a box and opens its location view.
2. The system retrieves the latest valid location observation.
3. The interface shows a marker on the map with the observation time.
4. The user checks the timestamp to judge whether the position is recent.

**Alternative flows:**

- No valid location has been received: display location unavailable.
- The device stops reporting: show the last known location with its age and the device's stale contact status.
- A GPS fix is unavailable: do not make a previous coordinate appear newly measured.
- Map service fails: show available coordinates and the observation time in text.
- Simulated location is used in development: label the displayed data as simulated.

**Postcondition:** The user sees a timestamped last known location or an explicit unavailable state. The system does not
imply that stale coordinates are the box's current position.

### UC-05 — Review lid-event history

**Primary actor:** Authorised user  
**Goal:** Review when the box was opened or closed.  
**Preconditions:** The user is signed in and has access to the box.  
**Trigger:** The user opens the history view.  
**Requirements:** FR-02, FR-04, FR-07, FR-10

**Main flow:**

1. The user selects a box and opens its history.
2. The user selects a start and end time.
3. The system validates the interval and retrieves matching events.
4. The interface displays each transition and its observation time in chronological order.
5. The user changes the interval if needed.

**Alternative flows:**

- No matching events: show an empty state rather than an error.
- Invalid interval: ask the user to correct it.
- Delayed upload: include the event at its original observation time when the history is refreshed.
- An initial state snapshot is displayed: label it separately from opening/closing transitions.

**Postcondition:** The user can inspect recorded lid activity for the chosen interval. The history does not establish
who opened the box.

### UC-06 — Recover after a network interruption

**Primary actor:** Smart Box device  
**Goal:** Transfer buffered observations after connectivity is restored.  
**Preconditions:** FR-09 is included; pending observations have been saved within the supported buffer capacity.  
**Trigger:** The device reconnects to the backend.  
**Requirements:** FR-08, FR-09, FR-10

**Main flow:**

1. The device establishes an authenticated connection.
2. It sends pending observations while preserving their identifiers and original times.
3. The backend validates and stores each observation without duplicates.
4. The backend acknowledges accepted observations.
5. The device removes or marks acknowledged items as delivered.
6. The dashboard reflects restored contact and the latest available observations.

**Alternative flows:**

- Connection fails again: retain unacknowledged observations for a later retry.
- An acknowledgement is lost: resend the same observation identifier safely.
- An older observation arrives after a newer one: add it to history without replacing the newer state.
- Local storage reaches capacity: follow an explicitly agreed overflow policy; do not silently claim that all events
  were retained.

**Postcondition:** Successfully acknowledged observations are stored centrally once. Reconnection alone does not make an
old GPS fix fresh.

## 7. Requirement-to-use-case traceability

| Requirement | Related use cases          |
|-------------|----------------------------|
| FR-01       | UC-01                      |
| FR-02       | UC-01, UC-02, UC-04, UC-05 |
| FR-03       | UC-02                      |
| FR-04       | UC-03, UC-05               |
| FR-05       | UC-04                      |
| FR-06       | UC-04                      |
| FR-07       | UC-05                      |
| FR-08       | UC-02, UC-04, UC-06        |
| FR-09       | UC-03, UC-06               |
| FR-10       | UC-03, UC-05, UC-06        |
| FR-11       | UC-02                      |

## 8. Optional features and exclusions

| Feature                                 | Proposed treatment                             | Reason                                                                     |
|-----------------------------------------|------------------------------------------------|----------------------------------------------------------------------------|
| Remote lock/unlock                      | Unresolved; excluded from the initial baseline | Requires confirmation of the intended behaviour and physical lock hardware |
| Battery-level display                   | Could have                                     | Requires a supported way to measure battery state                          |
| Location route history                  | Could have                                     | Last-known location is the initial user-facing requirement                 |
| Email or push alerts                    | Could have                                     | Dashboard status is sufficient for the initial scope                       |
| Equipment inventory                     | Won't have in this iteration                   | Contents tracking has not been requested or defined                        |
| Patient information                     | Won't have in this iteration                   | The current scope is equipment monitoring                                  |
| User registration and administration UI | Won't have in this iteration                   | Accounts and permissions can initially be provisioned by the team          |

## 9. Document basis and acknowledgement

AI assistance: OpenAI ChatGPT assisted with structuring this document.
