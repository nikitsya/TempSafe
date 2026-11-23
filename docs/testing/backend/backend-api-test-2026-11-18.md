# TempSafe · Backend API test · 18 November 2026

I tested the backend on `master` at commit `ac3af19` (after PR #31) on a local copy, never on tempsafe.app. MySQL
8.0 ran locally with `database/schema.sql` and migrations 001 and 002. I added two test users: **alice**, assigned to
TS-01, and **bob**, with no box. There was also a second box, **TS-02**. Requests went through the FastAPI app, the
same way as the project's own tests, with `MQTT_ENABLED=false`.

## Re-run on 21 November 2026

After PR #32 (limits over MQTT) and PR #33 (dual-sensor ingestion), I ran both again on `master` at `60f8f24`:
**180 passed** in the project suite and **31 passed, 0 failed** in the exploratory checks. B-23 now has a backend
answer: the selected limits are published to the box over MQTT. It is still open on the box itself until the device
part (`feature/device-configuration-sync`) is merged and running on the Pi.

## Summary

| Check                                 | Result                           |
|---------------------------------------|----------------------------------|
| Project test suite (`tests/backend`)  | **152 passed**, 0 failed (3.4 s) |
| Exploratory API checks (B-01 to B-36) | **31 passed**, 0 failed, 5 notes |

No check failed. The backend refuses every invalid request I tried, keeps users to their own box, classifies the
limits exactly as FR-05 says and handles retries and delayed uploads as FR-10 requires. The five notes are open
questions for the team, not crashes or data loss.

## Passed

| ID   | Check                                                                        | Evidence                                                                                                                                                                                  |
|------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| B-01 | History without signing in is refused                                        | `GET /api/boxes/TS-01/readings` → 401                                                                                                                                                     |
| B-02 | Reading list without signing in is refused                                   | `GET /api/readings` → 401                                                                                                                                                                 |
| B-03 | Wrong password is refused                                                    | 401, *Invalid username or password*                                                                                                                                                       |
| B-04 | An unknown user gets the same message as a wrong password                    | 401, same message, so user names cannot be guessed                                                                                                                                        |
| B-05 | The sign-in cookie is protected                                              | `HttpOnly; Max-Age=28800; SameSite=strict; Secure`                                                                                                                                        |
| B-06 | The account shows the assigned box                                           | `/api/me` → `{"username": "alice", "box_ids": ["TS-01"]}`                                                                                                                                 |
| B-07 | A user without the box cannot read its history                               | bob → 404 *Box not found*                                                                                                                                                                 |
| B-08 | A box that is not assigned looks the same as an unknown box                  | alice → TS-02: 404; unknown box: 404                                                                                                                                                      |
| B-09 | SQL text in the box ID returns nothing                                       | `TS-01' OR '1'='1` → 404                                                                                                                                                                  |
| B-10 | A user without the box cannot change its limits                              | bob `PUT /configuration` → 404                                                                                                                                                            |
| B-11 | Upload without the device key is refused                                     | 401                                                                                                                                                                                       |
| B-12 | Upload with a wrong device key is refused                                    | 401                                                                                                                                                                                       |
| B-13 | The device cannot upload for another box                                     | 403 *Device cannot submit readings for this box*                                                                                                                                          |
| B-14 | Invalid uploads are refused                                                  | 422 for 80.01 °C, −40.01 °C, three decimals, an extra field, valid without temperature, sensor error with temperature, sequence as text, negative sequence and a time without a time zone |
| B-16 | Status at the exact limits (0 / 24 / 25 °C)                                  | −0.01 Alert, 0.00 Alert, 0.01 Normal, 23.99 Normal, 24.00 Warning, 25.00 Warning, 25.01 Alert, sensor error Unknown                                                                       |
| B-17 | An identical retry creates one reading and keeps its receipt time            | 200 / 200, same `received_at`                                                                                                                                                             |
| B-18 | Same sample ID with a different temperature is a conflict                    | 409                                                                                                                                                                                       |
| B-19 | A new sample ID with an existing sequence number is a conflict               | 409                                                                                                                                                                                       |
| B-20 | A delayed old Alert does not replace the latest reading                      | latest stays sequence 41, 21.00 °C Normal                                                                                                                                                 |
| B-21 | Limits in the wrong order are refused                                        | 422 for lower = warning, warning > upper, warning = upper, upper 81, missing upper                                                                                                        |
| B-22 | Saving the same limits twice does not create a second profile                | same profile ID both times                                                                                                                                                                |
| B-24 | A reading sent with the new profile ID is accepted and uses its limits       | 200, 21.0 °C → Warning with limits 2 / 20 / 22                                                                                                                                            |
| B-25 | Start date after end date is refused                                         | 422 *Invalid history date range*                                                                                                                                                          |
| B-26 | Only one of the two dates is refused                                         | 422                                                                                                                                                                                       |
| B-27 | Bad `limit` values are refused                                               | 422 for 0, 101, −1 and `abc`                                                                                                                                                              |
| B-29 | A reading with a future time is kept out of the Today filter                 | it appears only in the list without dates                                                                                                                                                 |
| B-30 | A sensor error becomes the latest reading; the box still counts as reporting | latest `sensor_error`, state Unknown; status `reporting`                                                                                                                                  |
| B-31 | The latest reading is chosen by sequence, not by a wrong future time         | latest sequence 70                                                                                                                                                                        |
| B-32 | After sign-out the session no longer works                                   | logout 204, then `/api/me` 401                                                                                                                                                            |
| B-33 | The health check works without signing in                                    | 200 `{"status": "ok"}`                                                                                                                                                                    |
| B-34 | No CORS header is sent to another website                                    | no `Access-Control-Allow-Origin`                                                                                                                                                          |

## Notes for the team

### B-23 · New limits from Settings are not used by the box yet

I saved new limits through the API (Minimum 2, Warning from 20, Maximum 22). Then the device sent 21.0 °C with the
profile ID that is written in `device/temperature_readings.py`. The reading was stored with the **old** profile (24 /
25) and shown as **Normal**. With the new limits it would be **Warning**.

This matches the note in `database/migrations/003_add_box_configuration.sql`: *a configuration selects the desired
profile; it does not confirm device adoption*. B-24 shows that the backend already handles the new profile
correctly once the box sends it. The open part is on the device: it should read
`GET /api/boxes/TS-01/configuration` and use that profile. The release backlog already has this as *Apply updated
temperature limits on the Pi*.

**Impact for users:** after a change in Settings, the website still shows statuses and alerts from the old limits.
The Settings page says *The website uses these limits for new readings once the box updates*, which is honest, but a
user may not know whether the box has updated.

### B-28 · Readings with an unreliable clock are missing from date-filtered history

A reading sent with `clock_reliable: false` (no observation time) appears in the plain list but not in **Today** or
any date. The filter uses `observed_at`, and that value is empty for these readings.

FR-03 allows an unreliable clock, and the website shows the receipt time for such readings. Today they disappear
from History, Alerts and the CSV download. Possible fix: for these readings, filter by `received_at`.

### B-15 · A time two days in the future is accepted

The device can store a reading whose `observed_at` is two days ahead. It does not change the latest reading (B-31)
and stays out of Today (B-29). On the future date it would show as history. A small check, such as refusing
readings more than a few minutes ahead, or marking their clock as unreliable, would keep wrong clocks out.

### B-35 · No limit on repeated wrong passwords

Thirty wrong passwords in a row all returned 401, and the correct password still worked straight after. Argon2
makes each guess slow, which helps. Rate limiting may already be set in the web server on tempsafe.app. That
should be checked there; I did not test the live site.

### B-36 · A full day of history needs about 27 requests

I added a full day at 30-second intervals (2,623 readings). Loading it through the API took 27 requests of 100 and
0.49 s on the local database. On the internet each request adds network time. Raising the maximum `limit`, for
example to 1000, would make History load in a few requests. This is a performance suggestion; nothing is wrong.

## How to repeat

1. Start MySQL with `database/schema.sql` and migrations 001 and 002, then run `python -m pytest tests/backend -v`.
2. Run [explore_api.py](explore_api.py) and then [explore_api_extra.py](explore_api_extra.py) from the project root
   with the same `.env` and a device key of at least 32 characters. They add test users alice and bob, box TS-02 and
   their own readings, so use an empty development database, never the hosted one.
