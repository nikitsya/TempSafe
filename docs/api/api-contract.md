# TempSafe API contract

## Temperature classification

[`temperature.py`](../../backend/temsafe/temperature.py) provides
`classify_temperature(temperature_c, quality, profile)`.
Pass the profile associated with the measurement. The function uses its stored
limits: `T <= lower_c` or `T > upper_c` is `Alert`; `warning_c <= T <= upper_c`
is `Warning`; values between `lower_c` and `warning_c` are `Normal`. Missing
temperatures and sensor errors return `Unknown`.

The latest-reading endpoint loads the sample's recorded profile and uses this
function to add `temperature_state` to its response. This state describes the
recorded temperature; it does not assess whether the reading is stale.

## Saving incoming readings

`ReadingCreate` in [`schemas.py`](../../backend/temsafe/schemas.py) validates the incoming fields. Use
`save_reading(db, reading)` from `temsafe.readings` with a validated `ReadingCreate`
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

| GET endpoint                            | Successful response                                                                                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `/api/boxes/{box_id}`                   | Box object: `box_id` and `name` (strings), `last_seen_at` (UTC timestamp or `null`).                                                                |
| `/api/boxes/{box_id}/readings/latest`   | Latest sample by highest `sequence_no`, including a sensor error; fields below.                                                                     |
| `/api/boxes/{box_id}/readings?limit=20` | Array of samples, descending `sequence_no`; no `temperature_state`, `profile` or `freshness`. Default limit 20, allowed 1–100. Empty history: `[]`. |

Use the box-specific endpoints for the dashboard, not `/api/readings`, which mixes boxes and sorts by receipt time.

| Sample field                        | JSON type                  | Meaning / frontend handling                                                                                          |
|-------------------------------------|----------------------------|----------------------------------------------------------------------------------------------------------------------|
| `sample_id`, `box_id`, `profile_id` | string                     | Sample, box and recorded profile identifiers.                                                                        |
| `sequence_no`                       | integer                    | Measurement order within a box; do not reorder by upload time.                                                       |
| `temperature_c`                     | decimal string or `null`   | Celsius. Check for `null` before `Number(value)`; never turn a missing value into zero.                              |
| `quality`                           | string                     | `valid` or `sensor_error`; an error means temperature is unknown.                                                    |
| `observed_at`                       | timestamp string or `null` | Measurement time; `null` when the device clock is unreliable.                                                        |
| `clock_reliable`                    | boolean                    | Whether the observation time can be used.                                                                            |
| `received_at`                       | timestamp string           | Server receipt time; always present, not a substitute for measurement time.                                          |
| `temperature_state`                 | string                     | Latest endpoint only: `Normal`, `Warning`, `Alert` or `Unknown`. Recorded temperature classification, not freshness. |
| `freshness`                         | string                     | Latest endpoint only: `fresh`, `stale` or `unknown`, calculated from observation time when requested.                |

`profile` is an object on the latest response only: `profile_id` is a string; `lower_c`, `warning_c` and `upper_c`
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

- Responses use ISO 8601 UTC timestamps ending in `Z`, including `last_seen_at`. Fractional seconds may be present.
  Parse the timezone directly and format local time for display; missing timestamps remain `null`.
- `freshness` uses server UTC time minus `observed_at`: 0–90 seconds inclusive is `fresh`; older is `stale`.
  Missing or unreliable observation time, or time in the future, produces `unknown`. Receipt time is not used.
  This describes sample age, not sensor health: a recent sensor error can be `fresh` with `temperature_state: Unknown`.
  It is evaluated on each request; the frontend must refresh or age the display rather than keep a cached result live.
- Intended contact rule: more than 180 seconds without authenticated contact means not reporting. Heartbeat updates
  are not implemented; `last_seen_at: null` means contact is unknown, not proof that the device is offline.
- Sensor errors remain explicit even when stale or not reporting. Receipt of an old buffered sample does not make it
  fresh.
- Handle HTTP status and `detail` together: `404` with `Box not found` is not the no-observations state. Invalid `limit`
  returns `422` with a validation-error array in `detail`. Network errors and `5xx` mean refresh failed; retain any
  previous data as historical, never present them as an empty history or a fresh Normal reading.

### Profile limits and remaining integration

The latest response includes `profile` from the sample's recorded profile, not the box's newest profile.
The dashboard displays these limits; no separate profile request is needed.
The seeded demo limits are 0/24/25°C; the unused legacy frontend fixture's 15°C lower limit is outdated.

The frontend adapter maps `temperature_c` to `temperatureC`, formats `observed_at` for display and derives reading
age using the browser clock.
Map valid temperature states to lower-case UI names; map `quality: sensor_error` to `sensor_error`. Handle no
observations
as `no_data`; `Unknown` must never become `normal`. Apply `freshness` separately; stale or unknown-age readings must not
appear live. The dashboard uses `fetch()` directly and reads the error body to distinguish the two `404` cases.
The shared `apiGet()` helper currently serves the health check and does not preserve error bodies.

Still pending: automatic refresh, using server-calculated freshness in the frontend, device-contact handling,
authentication and box access checks, phone-notification status and history date filters. Sample fields such as
`pushAlerts`, `lastValidC` and profile `name` are not supplied by the current API. A silence or acknowledgement action
is not part of these read endpoints.

## Other available endpoints

| Endpoint                        | Response                                                                                                      |
|---------------------------------|---------------------------------------------------------------------------------------------------------------|
| `GET /api/readings?limit=20`    | Samples across boxes, newest receipt time first; default limit 20, allowed 1–100. Empty result: `[]`.         |
| `GET /api/readings/{sample_id}` | One sample, without `temperature_state`; missing ID: `404` with `{"detail":"Temperature reading not found"}`. |
| `GET /api/health`               | `200` with `{"status":"ok"}`; checks the application, not MySQL.                                              |

Run the server using the [backend guide](../../backend/temsafe/README.md); inspect live schemas at `/docs`.
