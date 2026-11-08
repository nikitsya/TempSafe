# TempSafe frontend

The web interface of TempSafe, built with plain HTML, CSS and JavaScript (no build step).
The latest layout changes are recorded in
the [accessibility review](../docs/testing/accessibility/core-scenario-accessibility-review.md).
The [UI mock-ups](../docs/design/ui/ui-design.md) describe the wider target design.
The clickable design prototype stays in [`prototype/ui`](../prototype/ui); this folder is the
application frontend under development, served by the FastAPI backend in `backend/temsafe`.
Sign-in and sign-out use the backend session API. The dashboard and history request readings for
prototype box `TS-01`; the signed-in user must have access to that box. The dashboard polls every
five seconds and refreshes when the browser tab becomes visible. Reload history to fetch new readings.

The hosted application is available at [tempsafe.app](https://tempsafe.app).
Open the sign-in page and use an account provisioned by an operator. There is no self-registration
or password-reset form. See the [deployment notes](../docs/operations/deployment.md).

## Structure

| Path                   | Purpose                                                          |
|------------------------|------------------------------------------------------------------|
| `index.html`           | Sign-in page (entry point)                                       |
| `pages/dashboard.html` | Latest API reading for prototype box `TS-01`                     |
| `pages/history.html`   | Up to 100 readings, a temperature graph and excursion estimates  |
| `css/main.css`         | Shared styles: colour tokens, typography, layout and components  |
| `js/api.js`            | API helper and redirects to the sign-in page                     |
| `js/main.js`           | API connection check and sign-out handling                       |
| `js/sample-data.js`    | Legacy fixtures; not loaded by the application pages             |
| `js/dashboard.js`      | Dashboard status, details, freshness and automatic refresh       |
| `js/history.js`        | History table, temperature graph and estimated excursion periods |
| `js/signin.js`         | Form validation, login request and sign-in messages              |

## Authentication behaviour

The sign-in form sends the username and password as JSON to `POST /api/login`, keeping the password
out of the URL. A 204 response opens the dashboard; incorrect credentials or connection failures
show a message on the sign-in page. The backend manages an HttpOnly session cookie.

A 401 response to the dashboard or history readings request redirects to sign-in. The backend
checks box access; loading an HTML page alone does not grant access to readings. Sign out calls
`POST /api/logout` and redirects only after a 204 response. If sign-out fails, the page shows an
error and allows another attempt.

## History behaviour and limitations

History requests the latest 100 samples in descending measurement sequence. It shows a readings
table, a temperature graph and estimated periods outside the limits. These estimates cover the
loaded samples, not the box's complete history.

The current frontend fetches the latest reading's profile and uses its limits across the history
view. Although the history API returns each sample's recorded profile and classification, the
frontend does not yet use those fields for historical thresholds. If profiles change, earlier
samples can therefore be shown against the wrong limits. This remains an integration task.

The interface is fixed to `TS-01`; there is no box selector or settings form.

## How to run

Complete the [backend setup](../README.md#backend-development) and [database setup](../database/README.md),
including any required migrations. Provision an account with access to `TS-01` using the
[authentication guide](../docs/api/api-contract.md#provision-a-prototype-account). Then run from the
repository root with the project virtual environment activated:

```bash
python -m uvicorn temsafe.main:app --reload --app-dir backend
```

Open http://127.0.0.1:8000 in a browser and sign in. Serve the pages through FastAPI rather than
opening the HTML files directly. The session cookie has the `Secure` attribute; use local HTTPS if
your browser does not accept it on the loopback address.

The status line shows "API connected" when `GET /api/health` returns `{"status": "ok"}`. This checks
application availability, not MySQL, the sensor or whether the user is signed in.
