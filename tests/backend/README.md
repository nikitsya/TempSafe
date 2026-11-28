# Backend tests

The pytest suite covers database access, API responses, temperature classification,
payload validation and reading storage, including retries and conflicts.
Dual-sensor checks cover legacy `inside` defaults, rejected locations, shared
sequence conflicts, separate history/latest queries, outside samples without
box-limit classification, and inside freshness unaffected by outside receipts.
Device queue tests are supplied separately to the hardware owner; see the
[team handover](../../docs/operations/dual-sensor-rollout.md#device-handover).

## Before you start

Complete the [backend setup](../../README.md#backend-development) and
[database setup](../../database/README.md). Use the project's `.venv` and configure
`.env`. MySQL must be running for the full suite.

Use an isolated development database, never the hosted database. Database tests create
temporary records and remove them through rollback or explicit clean-up. Set `MQTT_ENABLED=false`
for this suite; MQTT tests mock storage and do not require the production broker.

## Run the tests

From the project root, with `.venv` activated:

```sh
python -m pytest tests/backend -v
```

To run one test file, specify its path instead:

```sh
python -m pytest tests/backend/test_save_reading.py -v
```

## Test files

| File                             | Coverage                                                                                                      |
|----------------------------------|---------------------------------------------------------------------------------------------------------------|
| `test_auth.py`                   | Login, session expiry/revocation, box assignments and device credentials.                                     |
| `test_configuration.py`          | Assigned-box access, versioned thresholds and publication of the selected MySQL profile.                      |
| `test_configuration_delivery.py` | Retained payloads, commit ordering, reconnects, retries and current-profile selection without a broker.       |
| `test_database.py`               | Database connection, stored reading retrieval and missing readings.                                           |
| `test_boxes.py`                  | Box responses and unknown boxes.                                                                              |
| `test_readings.py`               | Reading lists and limit validation.                                                                           |
| `test_latest_reading.py`         | Latest readings, recorded profiles, UTC/freshness, box history and sequence order.                            |
| `test_save_reading.py`           | Input validation, storage, retries, conflicts and POST responses.                                             |
| `test_mqtt.py`                   | MQTT validation, topic checks and acknowledgement after storage (mock storage).                               |
| `test_push.py`                   | Browser subscriptions, box assignments, state transitions, delivery retries, expiry and worker configuration. |
| `test_settings.py`               | Environment defaults, legacy setting names, overrides and permitted push-provider hosts.                      |
| `test_temperature.py`            | Temperature thresholds and sensor errors.                                                                     |

A successful run has no failures or errors. If a test fails, inspect the error and
check the database connection, table setup and selected Python environment.

Run the backend confirmation tests with `python -m pytest tests/backend`.
For physical Pi reconnect, restart and output checks, follow the
[configuration rollout](../../docs/operations/mqtt.md#configuration-rollout).
