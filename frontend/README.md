# TEMSAFE frontend

Author: Maryna Hordiienko

The web interface of TEMSAFE, built with plain HTML, CSS and JavaScript (no build step).
It follows the revised mock-ups in [`docs/design/ui-design.md`](../docs/design/ui-design.md)
and the values in [`docs/design/ui-style-guide.md`](../docs/design/ui-style-guide.md).
The clickable design prototype stays in [`prototype/ui`](../prototype/ui); this folder is the
starting point of the real application that will use the FastAPI backend in `backend/temsafe`.

## Structure

| Path                   | Purpose                                                          |
|------------------------|------------------------------------------------------------------|
| `index.html`           | Sign-in page (entry point)                                       |
| `pages/dashboard.html` | Current status of the assigned box                               |
| `pages/history.html`   | Temperature history with date filter, graph and table            |
| `css/main.css`         | Shared styles: colour tokens, typography, layout and components  |
| `js/api.js`            | Small helper for calls to the backend API (`/api/...`)           |
| `js/main.js`           | Page start-up code, including the API connection check           |
| `assets/icons/`        | Icons and images used by the interface                           |

## How to open

- **Without the backend:** open `index.html` in a browser. The page shows
  "API not reachable", which is expected.
- **With the backend:** the status line shows "API connected" when `GET /api/health`
  returns `{"status": "ok"}`. This works once the frontend is served by FastAPI (next step),
  because a page opened directly from disk is blocked by the browser's CORS rules.

## Next steps

1. Implement sign-in against the backend authentication endpoint.
2. Load the latest reading and freshness state on the dashboard.
3. Load history data and draw the graph and table.
4. Serve the frontend from FastAPI so that it uses the same HTTPS origin as the API.
