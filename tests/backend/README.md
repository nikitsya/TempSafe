# Backend tests

To run all backend tests, use `tests/backend` instead of
`tests/backend/test_database.py` in the commands below. The full suite currently
has **22 tests**, including reading lists, invalid limits and box responses.
The latest-reading and box-history tests use MySQL to check delayed uploads,
measurement order, limits, box isolation, sensor errors and missing data.
Their temporary records are rolled back.

These pytest tests check the MySQL connection and save one test measurement,
read it back through SQLAlchemy and the API, then remove the test records.
They also check that an unknown sample ID returns HTTP 404.

## Before you start

1. Complete the [backend setup](../../README.md#backend-development), including
   the development dependencies in the project’s `.venv`.
2. Set your database connection details in the project root `.env`, using
   [`.env.example`](../../.env.example) as a reference.
3. Start your MySQL server and ensure the project tables exist. See the
   [database setup guide](../../database/README.md) if needed. Docker Desktop
   is not required.

## Run the tests

From the **Smart-Box project root**, use the command for your system:

**macOS / Linux**

```sh
.venv/bin/python -m pytest tests/backend/test_database.py -v
```

**Windows**

```text
.venv\Scripts\python.exe -m pytest tests/backend/test_database.py -v
```

Alternatively, use your editor’s pytest runner with the project’s `.venv`
interpreter and select `test_database.py`. In PyCharm, a Python run configuration
can use module `pytest`, parameters `tests/backend/test_database.py -v` and the
project root as its working directory.

## Expected result

```text
test_database_connection PASSED
test_measurement_is_written_and_read_back PASSED
test_missing_reading_returns_404 PASSED
```

The summary should show **3 passed**. If a test fails, check that MySQL is running,
the `.env` settings are correct and your editor uses the project’s `.venv`.
