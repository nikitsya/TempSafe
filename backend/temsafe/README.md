# Run the backend locally

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

`GET /api/boxes/{box_id}` returns a box's ID, name and last contact time, or
`404` if it does not exist. Try it in `/docs` with an existing `box_id`.
This prototype endpoint does not yet check user access.

`GET /api/readings` returns up to 20 samples, ordered by receipt time (newest
first). Use `/api/readings?limit=5` to change the number, from 1 to 100. An empty
database returns `[]`. These prototype reading routes do not yet check user access.

- [Website](http://127.0.0.1:8000) — the frontend.
- [API documentation](http://127.0.0.1:8000/docs) — choose an endpoint, click **Try it out**, enter any required values
  and click **Execute**.
- [Health check](http://127.0.0.1:8000/api/health) — returns `{"status":"ok"}`
  when the application is running; it does not check MySQL.

Keep the server running while using the site. `--reload` restarts it when Python
files change. To stop it, use your editor's Stop button or press **Ctrl+C** in
the terminal.
