# TempSafe UI prototype

Author: Maryna Hordiienko

A clickable HTML/CSS/JavaScript prototype of the TempSafe web application. It uses synthetic data only and does not connect to the backend. It is used to check the UI design and to run automated browser tests before the FastAPI application exists.

## Pages

| File | Screen |
|---|---|
| `login.html` | Sign in (test account `paramedic` / `demo`; `nobox` / `demo` shows denied access) |
| `dashboard.html?state=...` | Current status. States: `normal`, `warning`, `alert`, `stale`, `sensor`, `offline`, `network`, `empty`, `denied` |
| `history.html` | History with time filter, graph, gaps and readings table |
| `style.css` | Shared styles from `docs/design/ui-style-guide.md` |

## How to open

Open `login.html` in a browser. No server or build step is needed.

## Automated tests

See `docs/testing/browser-test-plan.md`.

```bash
cd prototype/ui
npm init -y
npm install -D @playwright/test
npx playwright install chromium
npx playwright test
```
