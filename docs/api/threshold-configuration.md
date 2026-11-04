# Operator threshold configuration API

This backend feature lets an operator select new temperature limits for a box.
It does not add user login, frontend controls, heartbeat settings or device delivery.
The Raspberry Pi currently uses local constants; saving this configuration does
not prove that the device has received or adopted it.

## Access and setup

The two routes require `Authorization: Bearer <operator-token>`. Configure
`TEMSAFE_CONFIG_ADMIN_TOKEN` with a cryptographically random value of at least
32 characters in the backend environment. Restart the backend after changing it.
An absent or short configured token disables these routes (`503`); missing or
incorrect client credentials return `401`. Use HTTPS when accessing a remote server.

This token grants configuration access to **all boxes**. It is an interim operator
credential, not user authentication or per-box role-based authorisation. Keep it
out of Git, URLs, browser JavaScript and screenshots. Other existing API routes
are not secured by this change. Before frontend integration, implement user
sessions and permission checks rather than distributing the operator token.

For a fresh database, use the updated `database/schema.sql`. For an existing
database, back up first and run
[003_add_box_configuration.sql](../../database/migrations/003_add_box_configuration.sql)
once. Do not run this migration after the updated baseline: the table already exists.
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

Tests use isolated MySQL and cover disabled access, missing/incorrect credentials,
invalid and unordered limits, missing boxes, unchanged retries, active-profile
retrieval and preservation of an earlier sample's classification. The current
backend suite passed 128 tests after this change. No production migration or
Raspberry Pi change was performed.
