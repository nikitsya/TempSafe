# Backend tests

The pytest suite covers database access, API responses, temperature classification,
payload validation and reading storage, including retries and conflicts.

## Before you start

Complete the [backend setup](../../README.md#backend-development) and
[database setup](../../database/README.md). Use the project's `.venv` and configure
`.env`. MySQL must be running for the full suite.

Use an isolated development database, never the hosted database. Database tests create
temporary records and remove them through rollback or explicit cleanup. Set `MQTT_ENABLED=false`
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

| File                     | Coverage                                                                           |
|--------------------------|------------------------------------------------------------------------------------|
| `test_auth.py`           | Login, session expiry/revocation, box assignments and device credentials.          |
| `test_configuration.py`  | Operator access, versioned thresholds and per-box heartbeat settings.              |
| `test_database.py`       | Database connection, stored reading retrieval and missing readings.                |
| `test_boxes.py`          | Box responses and unknown boxes.                                                   |
| `test_readings.py`       | Reading lists and limit validation.                                                |
| `test_latest_reading.py` | Latest readings, recorded profiles, UTC/freshness, box history and sequence order. |
| `test_save_reading.py`   | Input validation, storage, retries, conflicts and POST responses.                  |
| `test_mqtt.py`           | MQTT validation, topic checks and acknowledgement after storage (mock storage).    |
| `test_temperature.py`    | Temperature thresholds and sensor errors.                                          |

A successful run has no failures or errors. If a test fails, inspect the error and
check the database connection, table setup and selected Python environment.
