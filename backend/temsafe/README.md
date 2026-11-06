# TempSafe backend

See the [API contract](../../docs/api/api-contract.md) for endpoints, fields, examples and integration status.

## Hosted backend

The application at [tempsafe.app](https://tempsafe.app) runs this backend as the `tempsafe`
systemd service on AWS EC2. Nginx forwards HTTPS requests to Uvicorn on `127.0.0.1:8000`.
See the [deployment notes](../../docs/operations/deployment.md) for service checks.
The commands below are for local development; the hosted service runs without `--reload`.

## Setup

First, complete the [backend setup](../../README.md#backend-development).

## In PyCharm

Create a **Python** run configuration:

| Setting           | Value                             |
|-------------------|-----------------------------------|
| Name              | `Run backend`                     |
| Interpreter       | Python from the project's `.venv` |
| Run target type   | `Module`                          |
| Module name       | `uvicorn`                         |
| Parameters        | `temsafe.main:app --reload`       |
| Working directory | The TempSafe project root         |

Click **Run** and wait for `Application startup complete`.

## In any terminal

From the project root, with `.venv` activated, run:

```sh
python -m uvicorn temsafe.main:app --reload
```

## Open in your browser

- [Website](http://127.0.0.1:8000) — the frontend.
- [API documentation](http://127.0.0.1:8000/docs) — inspect and try requests.
- [Health check](http://127.0.0.1:8000/api/health) — returns `{"status":"ok"}`; it does not check MySQL.

Keep the server running while using the site. Stop it with **Ctrl+C**.

## MQTT lifecycle

FastMQTT starts with FastAPI when `MQTT_ENABLED=true`. Leave it disabled for HTTP-only development.
Configure broker credentials in the environment; see the [MQTT guide](../../docs/operations/mqtt.md).
Use one Uvicorn worker and no production reload. The separate MQTT worker service is no longer used.
