# TempSafe API contract

## Authentication

- `POST /api/login` accepts JSON fields `username` and `password`. Success returns 204
  and an eight-hour, host-only session cookie with Secure, HttpOnly and SameSite=Strict.
  Use HTTPS. Incorrect credentials return 401.
- `POST /api/logout` revokes the server-side session and clears the cookie. It returns 204.
- Box and reading queries require a current session (401 otherwise). Lists contain only
  assigned boxes' samples. Requests for unassigned boxes or samples return 404.
  Threshold configuration also require the operator bearer token.
- `POST /api/readings` requires the `X-Device-Key` header. Set `TEMPSAFE_DEVICE_KEY` in
  the server environment to a separate randomly generated secret of at least 32 characters
  and set `TEMPSAFE_DEVICE_BOX_ID` to the authorised box. Missing or invalid credentials
  return 401. A valid key used for another box returns 403. The Raspberry Pi MQTT publisher
  continues to use its broker credentials. `GET /api/health` remains public.

### Provision a prototype account

For an existing database, apply [migration 004](../../database/migrations/004_add_user_sessions.sql)
once after backing up MySQL, only if `user_sessions` is missing. Fresh installations already include it.
Apply any other outstanding migrations in the [database guide](../../database/README.md).
Install the project dependencies. From the project root, run the following with the
project virtual environment active. Enter a new username and a password when prompted.
The example grants access to the existing prototype box. Both inserts commit together.
Use a new identifier of at most 191 characters and a password of at most 1,024 characters,
matching the login endpoint limits. This creates an account; it does not reset an existing password.

```sh
python - <<'PYTHON'
from getpass import getpass
from argon2 import PasswordHasher
from tempsafe.db.session import SessionLocal
from tempsafe.db.models import AppUser, BoxAccess

username = getpass("New username (hidden): ").strip()
password = getpass("New password: ")
if not username or not password:
    raise SystemExit("A username and password are required.")
with SessionLocal.begin() as db:
    user = AppUser(auth_subject=username, password_hash=PasswordHasher().hash(password))
    db.add(user)
    db.flush()
    db.add(BoxAccess(user_id=user.user_id, box_id="TS-01"))
PYTHON
```

## Temperature classification

[`temperature.py`](../../backend/tempsafe/monitoring/temperature.py) provides
`classify_temperature(temperature_c, quality, profile)`.
Pass the profile associated with the measurement. The function uses its stored
limits: `T <= lower_c` or `T > upper_c` is `Alert`; `warning_c <= T <= upper_c`
is `Warning`; values between `lower_c` and `warning_c` are `Normal`. Missing
temperatures and sensor errors return `Unknown`.

The latest-reading and box history endpoints classify each sample using its recorded profile.
Use each history row’s `temperature_state` and `profile` for the table, graph and excursion periods.
A later change to the box’s limits preserves the interpretation of earlier readings.

## Saving incoming readings

`ReadingCreate` in [`schemas.py`](../../backend/tempsafe/schemas.py) validates the incoming fields. Use
`save_reading(db, reading)` from `tempsafe.monitoring.readings` with a validated `ReadingCreate`
and a dedicated `SessionLocal()` session. The function checks the box and profile,
then uses `add()`, `commit()` and `refresh()` to save the sample.

Observation times must include a timezone and are stored as UTC. Receipt time is
set by the backend. Valid temperatures must be between -40 and 80°C with at most
two decimal places; sensor errors require `null`. An unreliable clock requires
`observed_at: null`. Sample and profile IDs must be UUIDs.

An identical retry returns the existing sample without changing its receipt time.
Reusing its ID or box sequence with different data raises `ValueError`. Missing
boxes and profiles also raise `ValueError`; invalid payloads fail Pydantic validation.
The function commits its session, so keep unrelated changes in another session.

`POST /api/readings` accepts a JSON `ReadingCreate` payload and calls this function.
It returns the stored reading with `200 OK`, both for a new sample and an identical
retry. The response includes the server's `received_at` value. Unknown boxes or
profiles (including a profile belonging to another box) return `404`; conflicting
sample IDs or box sequence numbers return `409`; invalid payloads return `422`.

Example request body for `/docs` or an HTTP client:

```json
{
  "schema_version": 1,
  "sample_id": "3f927b1e-8261-4ad8-a45e-2ba89a016d14",
  "box_id": "TS-01",
  "sequence_no": 1,
  "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
  "observed_at": "2026-01-01T12:00:00Z",
  "clock_reliable": true,
  "temperature_c": "24.50",
  "quality": "valid"
}
```

## Dashboard API contract

Working integration contract based on the current backend; team review is pending.
Use relative `/api` URLs when served by FastAPI, locally or on AWS.

### Endpoints and fields available now

| GET endpoint                            | Successful response                                                                                                                                             |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/api/boxes/{box_id}`                   | Box object: `box_id` and `name` (strings).                                                                                                                      |
| `/api/boxes/{box_id}/readings/latest`   | Latest sample by highest `sequence_no`, including a sensor error; fields below.                                                                                 |
| `/api/boxes/{box_id}/readings?limit=20` | Array of samples, descending `sequence_no`; each includes its recorded `profile` and `temperature_state`. Default limit 20, allowed 1–100. Empty history: `[]`. |

Use the box-specific endpoints for the dashboard, not `/api/readings`, which mixes boxes and sorts by receipt time.

| Sample field                        | JSON type                  | Meaning / frontend handling                                                                           |
|-------------------------------------|----------------------------|-------------------------------------------------------------------------------------------------------|
| `sample_id`, `box_id`, `profile_id` | string                     | Sample, box and recorded profile identifiers.                                                         |
| `sequence_no`                       | integer                    | Measurement order within a box; do not reorder by upload time.                                        |
| `temperature_c`                     | decimal string or `null`   | Celsius. Check for `null` before `Number(value)`; never turn a missing value into zero.               |
| `quality`                           | string                     | `valid` or `sensor_error`; an error means temperature is unknown.                                     |
| `observed_at`                       | timestamp string or `null` | Measurement time; `null` when the device clock is unreliable.                                         |
| `clock_reliable`                    | boolean                    | Whether the observation time can be used.                                                             |
| `received_at`                       | timestamp string           | Server receipt time; always present, not a substitute for measurement time.                           |
| `temperature_state`                 | string                     | Latest and history endpoints: `Normal`, `Warning`, `Alert` or `Unknown`.                              |
| `freshness`                         | string                     | Latest endpoint only: `fresh`, `stale` or `unknown`, calculated from observation time when requested. |

`profile` accompanies the latest reading and each box history row: `profile_id` is a string; `lower_c`, `warning_c` and
`upper_c`
are decimal strings in Celsius. It matches the reading’s `profile_id`, including for sensor errors.

### Example responses

Latest valid reading — `200 OK` (synthetic response at 12:00:05 UTC on 1 November 2026):

```json
{
  "sample_id": "3f927b1e-8261-4ad8-a45e-2ba89a016d14",
  "box_id": "TS-01",
  "sequence_no": 1,
  "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
  "observed_at": "2026-11-01T12:00:00Z",
  "clock_reliable": true,
  "received_at": "2026-11-01T12:00:05Z",
  "temperature_c": "24.50",
  "quality": "valid",
  "temperature_state": "Warning",
  "freshness": "fresh",
  "profile": {
    "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
    "lower_c": "0.00",
    "warning_c": "24.00",
    "upper_c": "25.00"
  }
}
```

Latest sensor error — `200 OK` (response at 12:00:35 UTC on the same day); do not replace it with an older valid sample:

```json
{
  "sample_id": "8b027b1e-8261-4ad8-a45e-2ba89a016d14",
  "box_id": "TS-01",
  "sequence_no": 2,
  "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
  "observed_at": "2026-11-01T12:00:30Z",
  "clock_reliable": true,
  "received_at": "2026-11-01T12:00:35Z",
  "temperature_c": null,
  "quality": "sensor_error",
  "temperature_state": "Unknown",
  "freshness": "fresh",
  "profile": {
    "profile_id": "e93a4368-e11a-4f27-8b31-d55d61392548",
    "lower_c": "0.00",
    "warning_c": "24.00",
    "upper_c": "25.00"
  }
}
```

Known box with no observations — latest endpoint returns `404 Not Found`:

```json
{
  "detail": "No readings available for this box"
}
```

### Time, freshness and errors

- Responses use ISO 8601 UTC timestamps ending in `Z`. Fractional seconds may be present.
  Parse the timezone directly and format local time for display; missing timestamps remain `null`.
- `freshness` uses server UTC time minus `observed_at`: 0–90 seconds inclusive is `fresh`; older is `stale`.
  Missing or unreliable observation time, or time in the future, produces `unknown`. Receipt time is not used.
  This describes sample age, not sensor health: a recent sensor error can be `fresh` with `temperature_state: Unknown`.
  It is evaluated on each request; the frontend must refresh or age the display rather than keep a cached result live.
- Sensor errors remain explicit even when stale. Receipt of an old buffered sample does not make it
  fresh.
- Handle HTTP status and `detail` together: `404` with `Box not found` is not the no-observations state. Invalid `limit`
  returns `422` with a validation-error array in `detail`. Network errors and `5xx` mean loading failed. The current
  history page shows an error. The dashboard retains its last response when available, continues
  ageing it and shows a refresh-error banner; without a previous response it shows a loading error.

### Profile limits and remaining integration

The latest response includes `profile` from the sample's recorded profile, not the box's newest profile.
The dashboard displays these limits; no separate profile request is needed.
The seeded demo limits are 0/24/25°C; the unused legacy frontend fixture's 15°C lower limit is outdated.

The dashboard maps the API response and distinguishes the two `404` cases using the error body.
It currently derives age from the browser clock rather than consuming `freshness`. See the
[frontend guide](../../frontend/README.md#history-behaviour-and-limitations) for remaining UI work.

A silence or review
acknowledgement action is not part of these read endpoints.

## Other available endpoints

| Endpoint                        | Response                                                                                                      |
|---------------------------------|---------------------------------------------------------------------------------------------------------------|
| `GET /api/readings?limit=20`    | Samples across boxes, newest receipt time first; default limit 20, allowed 1–100. Empty result: `[]`.         |
| `GET /api/readings/{sample_id}` | One sample, without `temperature_state`; missing ID: `404` with `{"detail":"Temperature reading not found"}`. |
| `GET /api/health`               | `200` with `{"status":"ok"}`; checks the application, not MySQL.                                              |

Run the server using the [backend guide](../../backend/tempsafe/README.md); inspect schemas at `/docs`
on the local development server. The hosted Nginx configuration blocks public documentation routes.

## Operator configuration

The protected [threshold configuration API](threshold-configuration.md) creates and
selects versioned demo profiles. Its
operator token does not secure the other endpoints.
