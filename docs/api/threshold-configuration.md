# Operator threshold configuration API

An operator can set temperature limits and the desired heartbeat interval independently for each box.
The Raspberry Pi currently uses local constants; saving this configuration does
not prove that the device has received or adopted it.

## Access and setup

All configuration routes require a signed-in session assigned to the requested box and
`Authorization: Bearer <operator-token>`.
Configure
`TEMPSAFE_CONFIG_ADMIN_TOKEN` with a cryptographically random value of at least
32 characters in the backend environment. Restart the backend after changing it.
An absent or short configured token disables these routes (`503`); missing or
incorrect client credentials return `401`. Use HTTPS when accessing a remote server.

The operator token is a second credential for configuration changes and reads.
Keep it in the operator environment and out of browser JavaScript. See the
[authentication guide](api-contract.md#authentication) for account setup.

For a fresh database, use the updated `database/schema.sql`. For an existing
database, back up first and run
[003_add_box_configuration.sql](../../database/migrations/003_add_box_configuration.sql)
once if `box_configuration` is missing. Do not run this migration after the updated baseline:
the table already exists. Apply [migration 004](../../database/migrations/004_add_user_sessions.sql)
if `user_sessions` is absent and [migration 005](../../database/migrations/005_add_box_heartbeat_interval.sql)
if `boxes.heartbeat_interval_seconds` is absent.
The migration selects the existing profile only for boxes with exactly one profile.
Boxes with no profiles or several profiles remain unconfigured until an operator
sets their limits. Existing profiles and measurements are preserved.

## Routes

| Method and path                         | Behaviour                                                                                     |
|-----------------------------------------|-----------------------------------------------------------------------------------------------|
| `GET /api/boxes/{box_id}/configuration` | Return the selected desired profile; `404` if the box or selection is absent.                 |
| `PUT /api/boxes/{box_id}/configuration` | Create a new demo profile and select it atomically; return `200`. Missing boxes return `404`. |

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

## Heartbeat interval

Use `GET` or `PUT /api/boxes/{box_id}/configuration/heartbeat` with the same session
and operator token. Both return the desired interval as a JSON object. To request a
heartbeat every two minutes, send:

```json
{
  "heartbeat_interval_seconds": 120
}
```

Existing and new boxes default to 60 seconds. PUT accepts whole JSON integers from
1 to 65,535 seconds. Missing, extra or invalid fields return `422`. The box can
have a heartbeat setting before any temperature profile is selected. Changing the
interval preserves the profile, sampling rate and last contact time. Device
delivery and heartbeat reporting are separate work.

## Versioning and concurrency

`box_configuration` stores one selected `profile_id` per box. Its composite foreign
key prevents selecting another box's profile. Writes lock the box row, create the
profile and update the selection in one transaction. A failure rolls back both.
Concurrent writes are serialised; the last completed update becomes selected.
Sending the same settings as the currently selected profile returns that profile
without creating a duplicate. This is not general request-id deduplication after
intervening configuration changes.

Old profiles are never updated or deleted by these endpoints. Each sample retains
its recorded profile, so latest-reading classification remains historical even
when the operator selects different limits. Delayed uploads using an older valid
profile remain accepted. There is no device acknowledgement or configuration audit
of individual operators in this feature.

## Verification

Tests cover disabled access, missing/incorrect credentials, invalid and unordered limits,
missing boxes, unchanged retries, profile retrieval and historical classification. Heartbeat
tests cover independent intervals, invalid values and preservation of other settings. See
the [test guide](../../tests/backend/README.md).

The configuration table and heartbeat migration were deployed on 7 November 2026; see the
[deployment record](../operations/deployment.md). Access still requires a configured operator
token. These API changes do not change the Raspberry Pi’s local constants.
