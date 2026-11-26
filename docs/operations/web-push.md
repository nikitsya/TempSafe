# Web Push for box temperature changes

Apply migration 009 to an existing database, or initialise a new database from
the baseline. Apply the updated runtime grants. Set these variables in the
backend service environment before restarting it:

- `WEB_PUSH_PRIVATE_KEY` — protected path to a VAPID P-256 private PEM key.
- `WEB_PUSH_PUBLIC_KEY` — matching uncompressed P-256 public point in unpadded base64url.
- `WEB_PUSH_SUBJECT` — monitored `mailto:` contact for the push service.
- `WEB_PUSH_HOSTS` — optional comma-separated list of trusted push-provider
  hostnames. The defaults cover FCM, Mozilla and Apple. Approve additional exact
  provider hostnames before accepting subscriptions from other browsers.

## Browser integration

Use the signed-in session for these routes:

1. Fetch `GET /api/push/public-key` and pass the decoded `applicationServerKey`
   to the service worker registration's push manager when enabling notifications.
2. POST the browser's `subscription.toJSON()` to `/api/push/subscriptions`.
   Save the returned `id`. Re-registration for the same account updates its keys.
3. On disable or sign-out on a shared browser, DELETE
   `/api/push/subscriptions/{id}` and unsubscribe locally before ending the session.

The service worker receives JSON with `sample_id`, `box_id`, `state`,
`temperature_c` and UTC `observed_at`. Use the sample ID as the display tag
to collapse duplicate provider deliveries following a crash or network timeout.

Both HTTP and MQTT ingestion queue jobs in the measurement transaction. Fresh
inside readings are classified using their recorded profile. A new Warning or
Alert queues one job per enabled subscription belonging to an assigned user.
Immediately before sending, the worker checks access, the current episode and
the remaining freshness window. It also limits the provider TTL to that window.

## Delivery checks

Inspect application warnings or query MySQL without selecting endpoint URLs or
subscription keys:

```sql
SELECT id, sample_id, state, status, attempts, http_status, next_attempt
FROM push_deliveries ORDER BY id DESC LIMIT 30;
```

`accepted` means the push service accepted the request. Inspect `failed` rows
for permanent errors and `pending` rows for retries. Status 404 or 410 disables
the subscription. Superseded, expired or unauthorised jobs are cancelled.

For release verification, enable notifications on a supported phone, close the
site tab and trigger a fresh Warning followed by an Alert in a test box. Record
the observation time and the time each notification appears. Verify receipt
within 60 seconds and check that another reading in the same state stays quiet.
