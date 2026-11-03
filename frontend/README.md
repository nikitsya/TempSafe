# TempSafe frontend

The web interface of TempSafe, built with plain HTML, CSS and JavaScript (no build step).
The latest layout changes are recorded in
the [accessibility review](../docs/testing/core-scenario-accessibility-review.md).
The [UI mock-ups](../docs/design/ui-design.md) describe the wider target design.
The clickable design prototype stays in [`prototype/ui`](../prototype/ui); this folder is the
application frontend under development, served by the FastAPI backend in `backend/temsafe`.
Authentication is not implemented. The dashboard and history load readings for prototype box `TS-01`
from the backend API when each page opens. Refresh the page to fetch new readings.

The hosted application is available at [tempsafe.app](https://tempsafe.app).
Use the [dashboard link](https://tempsafe.app/pages/dashboard.html) to view the application;
the sign-in form does not authenticate users. See the [deployment notes](../docs/deployment.md).

## Structure

| Path                   | Purpose                                                         |
|------------------------|-----------------------------------------------------------------|
| `index.html`           | Sign-in page (entry point)                                      |
| `pages/dashboard.html` | Latest API reading for prototype box `TS-01`                    |
| `pages/history.html`   | Latest 20 API readings, ordered by measurement sequence         |
| `css/main.css`         | Shared styles: colour tokens, typography, layout and components |
| `js/api.js`            | Small helper for calls to the backend API (`/api/...`)          |
| `js/main.js`           | Page start-up code, including the API connection check          |
| `js/sample-data.js`    | Legacy fixtures; not loaded by the application pages            |
| `js/dashboard.js`      | Draws the dashboard status card, details and warning messages   |
| `js/history.js`        | Loads and renders the accessible readings table                 |
| `js/signin.js`         | Sign-in form handler (keeps the password out of the page URL)   |
| `assets/icons/`        | Icons and images used by the interface                          |

## How to run

Complete the [backend setup](../README.md#backend-development) and [database setup](../database/README.md),
then run from the repository root with the project virtual environment activated:

```bash
python -m uvicorn temsafe.main:app --reload --app-dir backend
```

Then open http://127.0.0.1:8000 in a browser. The status line shows "API connected"
when `GET /api/health` returns `{"status": "ok"}`; it does not check MySQL or the sensor.
