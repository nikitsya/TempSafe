# TEMSAFE frontend

Author: Maryna Hordiienko

The web interface of TEMSAFE, built with plain HTML, CSS and JavaScript (no build step).
It follows the revised mock-ups in [`docs/design/ui-design.md`](../docs/design/ui-design.md)
and the values in [`docs/design/ui-style-guide.md`](../docs/design/ui-style-guide.md).
The clickable design prototype stays in [`prototype/ui`](../prototype/ui); this folder is the
real application, served by the FastAPI backend in `backend/temsafe`.

## Structure

| Path                   | Purpose                                                         |
|------------------------|-----------------------------------------------------------------|
| `index.html`           | Sign-in page (entry point)                                      |
| `pages/dashboard.html` | Current status of the assigned box (sample data, `?state=...`)  |
| `pages/history.html`   | Temperature history                                             |
| `css/main.css`         | Shared styles: colour tokens, typography, layout and components |
| `js/api.js`            | Small helper for calls to the backend API (`/api/...`)          |
| `js/main.js`           | Page start-up code, including the API connection check          |
| `js/sample-data.js`    | Sample readings for each dashboard state until the API is ready |
| `js/dashboard.js`      | Draws the dashboard status card, details and warning messages   |
| `js/signin.js`         | Sign-in form handler (keeps the password out of the page URL)   |
| `assets/icons/`        | Icons and images used by the interface                          |

## How to run

From the repository root:

```bash
python -m pip install --user fastapi uvicorn
python -m uvicorn temsafe.main:app --reload --app-dir backend
```

Then open http://127.0.0.1:8000 in a browser. The status line shows "API connected"
when `GET /api/health` returns `{"status": "ok"}`.

The dashboard uses sample data. Choose a state with the URL, for example
http://127.0.0.1:8000/pages/dashboard.html?state=alert
(`normal`, `warning`, `alert`, `stale`, `sensor_error`, `not_reporting`, `no_data`).

Opening `index.html` directly from disk also works, but the status line then shows
"API not reachable", because the browser blocks requests from a local file to the API.