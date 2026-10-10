# TempSafe UI prototype

Author: Maryna Hordiienko

**Live prototype:** https://nikitsya.github.io/Smart-Box/prototype/ui/login.html
(test account `paramedic` / `demo`; synthetic data only)

A clickable HTML/CSS/JavaScript prototype of the TempSafe web application. It uses synthetic data only and does not connect to the backend. It is used to check the UI design and to run automated browser tests before the FastAPI application exists.

## Pages

| File | Screen |
|---|---|
| `login.html` | Sign in (test account `paramedic` / `demo`; `nobox` / `demo` shows denied access) |
| `dashboard.html?state=...` | Current status. States: `normal`, `warning`, `alert`, `stale`, `sensor`, `offline`, `network`, `empty`, `denied` |
| `history.html` | History with time filter, graph, gaps and readings table |
| `style.css` | Shared styles from [`ui-style-guide.md`](../../docs/design/ui-style-guide.md) |

## How to open

Use the live link above, or open `login.html` in a browser from a downloaded copy. No server or build step is needed.

## Automated tests

See [`browser-test-plan.md`](../../docs/testing/browser-test-plan.md). The tests are in `tests/ui.spec.js`.

```bash
cd prototype/ui
npm init -y
npm install -D @playwright/test
npx playwright install chromium
npx playwright test
```

On Windows PowerShell, use `npm.cmd` and `npx.cmd` if running scripts is disabled.
