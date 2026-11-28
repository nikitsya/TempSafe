# Dual-sensor backend rollout and team handover

The [device scripts](../../device/README.md) and [frontend](../../frontend/README.md)
now include dual-sensor support. The 21 November handover used a separate device
archive. The verification record below identifies which version was tested.

## Storage and compatibility

| Location             | Existing table        | Required change                                                                    |
|----------------------|-----------------------|------------------------------------------------------------------------------------|
| Raspberry Pi, SQLite | `readings`            | Device owner adds `sensor_location`, preserving `uploaded` and the shared counter. |
| Server, MySQL        | `temperature_samples` | Migration 007 adds `sensor_location` and indexes for sensor-filtered queries.      |

Locations are `inside` and `outside`. All legacy server rows and payloads without
the field mean `inside`. A new attempt gets its own UUID and the next **box-wide**
sequence number, regardless of sensor. Preserve both identifiers on retry; do not
initialise a separate queue or reset numbering for the outside sensor.

Outside samples retain the active box profile ID for provenance, but the API
returns `profile: null` and `temperature_state: null` for them. They must not
control the inside LED or buzzer. A sensor error remains an explicit failed
attempt with no temperature. Device contact includes receipts from either
sensor; box temperature freshness is based only on valid inside samples.

## Backend upgrade order

1. Back up MySQL and check whether `temperature_samples.sensor_location` exists.
   If absent, apply [migration 007](../../database/migrations/007_add_sensor_location.sql)
   once. Fresh installations use the updated baseline instead.
2. Deploy the reviewed backend. Confirm an old payload without location still
   stores as `inside`, and an explicit outside payload can be retrieved through
   `?sensor_location=outside`. Keep the existing TLS and topic permissions.
3. Before enabling outside collection, verify that the deployed frontend keeps
   the two sensors separate and accepts interleaved sequence numbers.
4. Back up the Pi's SQLite queue and deploy the matching device scripts together.
   Verify old pending inside rows before starting outside collection. Match fresh samples from both sensors to
   server records and matching `stored` acknowledgements.
5. Check reconnects, retries and process restarts on the Pi. Confirm the sequence
   counter and saved profile continue and an identical retry is stored only once.

The new publisher must follow the updated backend: an old strict backend rejects
the additional field. If rollback is needed, stop outside collection first and
preserve pending rows. Do not drop columns, reset identifiers or downgrade the
backend while an updated publisher is sending mixed-sensor data.

## Device handover

The 21 November archive contained complete proposed versions of `database.py`,
`models.py`, `configuration.py`, both temperature loggers and `mqtt_publisher.py`,
plus the device README, a patch relative to master `cbc60a5`, eight device tests
and their test dependencies.

The repository now contains the configuration subscriber, SQLite queue upgrade
and independent AM2302 logger on GPIO4. Both loggers record the adopted
profile ID. Only inside measurements drive the LED and buzzer. Follow the
[device guide](../../device/README.md) to run the loggers and publisher.

## Frontend handover

Use the [API contract](../api/api-contract.md#dashboard-api-contract) to verify the client after deployment.

- Request inside and outside data separately with `sensor_location`. Existing
  requests default to inside; paging must retain the selected sensor.
- Keep box status, temperature alerts and notifications based on inside data.
  Outside values are for comparison and have no box-limit classification.
- Check continuity for each sensor in
  `dashboard.js`, `history.js` and `notifications.js`. For one sensor, use reliable
  observation times: a gap over 90 seconds or unknown/backwards time breaks
  continuity. Sequence numbers remain the identifiers and pagination cursor.
- Display outside faults, missing data and stale measurements separately. Do not
  substitute outside readings when inside measurements are missing.
- Verify that CSV exports identify the sensor and that choosing another period
  prevents a late response from replacing the current data.

Example: inside samples numbered 100 and 102, measured 30 seconds apart, are
continuous when number 101 belongs to the outside sensor. They must not create
two alert periods or a missing-data band.

## Local verification — 21 November 2026

- 180 backend tests passed against isolated MySQL 8.4. Tests cover legacy defaults,
  invalid locations, duplicate conflicts, filtered history/latest queries,
  outside samples without box-limit classification and independent freshness.
- Migration 007 preserved a synthetic legacy MySQL sample and assigned `inside`.
  A fresh baseline and the upgraded database have matching column definitions
  and the same number of temperature-sample index entries.
- The separate device package passed eight tests using temporary SQLite queues.
  An upgraded copy of the supplied snapshot retained all 459 original rows and
  passed `PRAGMA integrity_check`; the original file was unchanged.
- A disposable Mosquitto broker carried 24 interleaved records from the proposed
  device queue through FastMQTT into MySQL: 12 per sensor, including an outside
  fault. Matching storage acknowledgements marked the rows uploaded. An identical
  retry produced another acknowledgement without inserting a duplicate record.

These checks used simulated sensor data and a local broker. They do not prove
physical AM2302 operation, hosted deployment or completion of frontend work.
