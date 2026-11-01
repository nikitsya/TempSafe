# TempSafe backend

See the [API contract](../../docs/api/api-contract.md) for endpoints, fields, examples and integration status.

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
| Working directory | The Smart-Box project root        |

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
