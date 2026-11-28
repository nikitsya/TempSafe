# TempSafe frontend

The web interface of TempSafe, built with plain HTML, CSS and JavaScript (no build step).
The latest layout changes are recorded in
the [accessibility review](../docs/testing/accessibility/core-scenario-accessibility-review.md).
The [UI mock-ups](../docs/design/ui/ui-design.md) describe the wider target design.
The [Figma examples](../ui-example/README.md) show the design prototype. FastAPI serves
the application in this directory.
Sign-in and sign-out use the backend session API. The dashboard and history request readings for
prototype box `TS-01`; the signed-in user must have access to that box. The dashboard polls every
five seconds and refreshes when the browser tab becomes visible. Reload history to fetch new readings.

The hosted application is available at [tempsafe.app](https://tempsafe.app).
Open the sign-in page and use an account provisioned by an operator. There is no self-registration
or password-reset form. See the [deployment notes](../docs/operations/deployment.md).

## Structure

| Path                   | Purpose                                                         |
|------------------------|-----------------------------------------------------------------|
| `index.html`           | Sign-in page (entry point)                                      |
| `pages/dashboard.html` | Latest API reading for prototype box `TS-01`                    |
| `pages/history.html`   | Readings by period: temperature graph or readings table         |
| `pages/alerts.html`    | Alert history and issues (sensor faults, no data) by period     |
| `pages/settings.html`  | View and change the temperature limits of the assigned box      |
| `css/main.css`         | Shared styles: colour tokens, typography, layout and components |
| `js/api.js`            | API helper and redirects to the sign-in page                    |
| `js/main.js`           | API connection check and sign-out handling                      |
| `js/sample-data.js`    | Legacy fixtures; not loaded by the application pages            |
| `js/dashboard.js`      | Dashboard status, details, freshness and automatic refresh      |
| `js/history.js`        | Periods, graph with issue bands, readings, alerts and issues    |
| `js/settings.js`       | Limits form, checks, confirmation step and save request         |
| `js/notifications.js`  | Pop-ups and browser notifications when an alert starts and ends |
| `js/signin.js`         | Form validation, login request and sign-in messages             |

## Authentication behaviour

The sign-in form sends the username and password as JSON to `POST /api/login`, keeping the password
out of the URL. A 204 response opens the dashboard; incorrect credentials or connection failures
show a message on the sign-in page. The backend manages an HttpOnly session cookie.

A 401 response to the dashboard or history readings request redirects to sign-in. The backend
checks box access; loading an HTML page alone does not grant access to readings. Sign out calls
`POST /api/logout` and redirects only after a 204 response. If sign-out fails, the page shows an
error and allows another attempt.

## Dashboard behaviour

The dashboard reads `GET /api/boxes/TS-01/readings/latest` every 5 seconds and
`GET /api/boxes/TS-01/status` for device contact. `not_reporting` shows **OFFLINE** with
the last contact time; `never_reported` shows **NOT CONNECTED**. A reading older than
90 seconds shows **LAST READING** with the old value in grey and its measurement time.

## History behaviour and limitations

**Today** (the default) and a chosen **Date** use
`start_date` and `end_date` (Irish calendar dates, observation time). History requests inside
and outside readings separately in pages of up to 100, following `before_sequence` for each sensor. **1 hour** requests
the dates it touches and keeps readings from the last hour. The graph uses a time axis; red bands mark sensor
faults and grey bands mark periods with no data (box offline or readings missing). The Alerts
page lists the same issues in a table. History also offers a CSV download for the chosen period. Inside readings are
classified with their recorded profiles. Outside readings are for comparison.
Time gaps over 90 seconds, unknown or backwards observation times, and sensor errors break
continuity. Interleaved sequence numbers are normal. Alert durations are estimates.

Other current limitations:

- Samples without a reliable observation time are not shown in History, because the API
  filters periods by observation time.
- The date picker offers the last 30 calendar days.
- The interface is fixed to `TS-01`; there is no box selector.

## Settings behaviour

Settings reads `GET /api/boxes/TS-01/configuration` and saves with `PUT` after the browser
checks the numbers (-40 to 80°C, two decimals, Too cold < Warning < Too hot) and the user
confirms the change. The page sends a fixed `source_note` ("Set on the TEMPSAFE website"). The backend
reuses the selected profile for identical settings. With MQTT enabled for this box, the
backend publishes the selection. The Pi uses the new limits for inside readings and local
alarms once it has validated and saved them. See the [configuration contract](../docs/api/threshold-configuration.md).

See the [consistency review](../docs/reviews/project-consistency-review.md) for reproducible examples.

## How to run

Complete the [backend setup](../README.md#backend-development) and [database setup](../database/README.md),
including any required migrations. Provision an account with access to `TS-01` using the
[authentication guide](../docs/api/api-contract.md#provision-a-prototype-account). Then run from the
repository root with the project virtual environment activated:

```bash
python -m uvicorn tempsafe.main:app --reload --app-dir backend
```

Open http://127.0.0.1:8000 in a browser and sign in. Serve the pages through FastAPI rather than
opening the HTML files directly. The session cookie has the `Secure` attribute; use local HTTPS if
your browser does not accept it on the loopback address.

To check API availability directly, open `/api/health`. MySQL connectivity, sensor freshness
and a signed-in user's access each need a separate check.

## Alert notifications

Every signed-in page checks the latest 100 readings every 15 seconds and announces two moments
once each: an alert starts ("Too hot — 26.4°C · 4 min", kept up to date while it lasts) and it
ends ("Back in range — 22.8°C"). The server classifies each inside reading using its recorded profile. They appear as a
pop-up on the website and, if the **Notifications** switch in Settings is on,
as a browser notification; clicking it opens Alerts.
On a first visit only an alert that is still on is announced. The state is stored in the browser.
The backend provides [Web Push subscriptions and delivery](../docs/operations/web-push.md).
Closed-tab notifications still require the frontend to register a service worker, subscribe
the browser and display incoming push messages.
