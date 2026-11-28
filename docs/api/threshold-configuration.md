# Box threshold configuration API

A signed-in user can set temperature limits for their assigned box. When MQTT is
enabled, the backend publishes the selected profile for `MQTT_BOX_ID` using the
[device configuration contract](../operations/mqtt.md#device-threshold-configuration-contract).
Saving this configuration does not prove that the device has received or adopted it.
The [Pi publisher](../../device/mqtt_publisher.py) saves validated limits in SQLite.
The backend accepts an applied-profile confirmation, but sending that message
after the local commit remains a device integration step.

## Access and setup

Use the existing sign-in cookie over HTTPS. Both routes check the box assignment.
An absent or expired session returns 401. An inaccessible box returns 404.
See the [authentication guide](api-contract.md#authentication) for account setup.

For a fresh database, use the updated `database/schema.sql`. For an existing
database, back up first and run
[003_add_box_configuration.sql](../../database/migrations/003_add_box_configuration.sql)
once if `box_configuration` is missing. Do not run this migration after the updated baseline:
the table already exists. Apply [migration 004](../../database/migrations/004_add_user_sessions.sql)
if `user_sessions` is absent.
Apply [migration 008](../../database/migrations/008_add_applied_profile.sql) if
`box_configuration.applied_profile_id` is absent. Migration 003 selects the
existing profile only for boxes with exactly one profile.
Boxes with no profiles or several profiles remain unconfigured until an assigned user
sets their limits. Existing profiles and measurements are preserved.

## Routes

| Method and path                         | Behaviour                                                                                                       |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `GET /api/boxes/{box_id}/configuration` | Return the selected desired profile; `404` if the box or selection is absent.                                   |
| `PUT /api/boxes/{box_id}/configuration` | Select the submitted settings atomically and return `200`. An unchanged submission reuses the selected profile. |

Example PUT body:

```json
{
  "lower_c": "0.00",
  "warning_c": "24.00",
  "upper_c": "25.00",
  "source_note": "Prototype limits agreed for the bench test."
}
```

All three limits must be finite, between -40 and 80 degrees Celsius, with no more
than two decimal places. They must satisfy `lower_c < warning_c < upper_c`.
`source_note` must contain non-whitespace text and be at most 2,000 characters.
Unknown fields are rejected. Invalid bodies return `422` without storing a profile.
These bounds follow the prototype's accepted measurement range, not medicine-storage
recommendations. New profiles always have `is_demo=true`.

Responses contain `profile_id`, `box_id`, all three limits, `source_note`,
`is_demo` and UTC `created_at`. Decimal values are serialised as strings.

## Versioning and concurrency

`box_configuration` stores one selected `profile_id` per box. Its composite foreign
key prevents selecting another box's profile. Writes lock the box row, create the
profile and update the selection in one transaction. A failure rolls back both.
Concurrent writes are serialised; the last completed update becomes selected.
Sending the same settings as the currently selected profile returns that profile
without creating a duplicate and requests publication again. This is not general request-id deduplication after
intervening configuration changes.

After a successful commit, the API wakes the configuration worker without waiting
for MQTT. The worker reads the currently selected profile from MySQL, rather than
keeping a potentially obsolete request payload. It locks the same box row as the
API while reading and queuing publication, so concurrent settings changes cannot
queue an older profile after a newer one. Run one backend worker as documented.

The selected profile in `box_configuration` is the durable source for retries;
the device confirmation column is added separately by migration 008. Publication repeats on connection and every 30
seconds,
including after a failed attempt or lost broker retained state. Each attempt has
a 10-second timeout. A failed MQTT attempt does not undo saved settings. With
`MQTT_ENABLED=false`, settings are saved without publication; enabling MQTT later
publishes the selected profile. Only the configured `MQTT_BOX_ID` is published by
this backend instance, even if the API manages other boxes.

Old profiles are never updated or deleted by these endpoints. Each sample retains
its recorded profile, so latest-reading classification remains historical even
when the user selects different limits. Delayed uploads using an older valid
profile remain accepted. The device confirmation is stored separately in `box_configuration.applied_profile_id`.
It starts as NULL and retains the last confirmed selection while a new one is pending.
An operator can compare both columns after the Pi receives the updated limits.

## Verification

Tests cover session and box access, invalid and unordered limits,
missing boxes, unchanged retries, profile retrieval and historical classification. See
the [test guide](../../tests/backend/README.md).

The configuration table was deployed on 7 November 2026; see the
[deployment record](../operations/deployment.md).
The [21 November deployment check](../operations/deployment.md#configuration-delivery-deployment--verified-21-november-2026)
verified retained publication over TLS. Checking local adoption and the return
confirmation on a physical Pi remains part of the [rollout](../operations/mqtt.md#configuration-rollout).
