# Check the MySQL connection with pytest

## Before running the test

1. Open the Smart-Box project in your preferred editor or terminal.
2. Select the project's `.venv` Python interpreter. The project and its development
   dependencies must be installed in this environment, including pytest,
   SQLAlchemy, MySQL Connector/Python and python-dotenv. See the
   [backend setup instructions](../../README.md#backend-development).
3. Ensure that the project root contains a local `../../.env` file. Use
   [`.env.example`](../../.env.example) as the reference and enter the credentials
   for your database. Do not commit passwords to Git.
4. Ensure that your MySQL server is running and reachable.
   If the database has not been set up yet, follow the
   [database setup guide](../../database/README.md), which includes instructions
   for initialising MySQL without Docker.

## Run from any editor or terminal

Open a terminal in the Smart-Box project root. These commands use the project's
Python interpreter directly, so activating the virtual environment is not required.

On macOS:

```sh
.venv/bin/python -m pytest tests/backend/test_database.py -v
```

On Windows:

```text
.venv\Scripts\python.exe -m pytest tests/backend/test_database.py -v
```

## Optional: configure the test in PyCharm

Open **Run > Edit Configurations** and add a **Python** configuration, or edit
your existing `test_database` configuration.

| Setting            | Value                                           |
|--------------------|-------------------------------------------------|
| Name               | `test_database`                                 |
| Python interpreter | The Python executable in this project's `.venv` |
| Run target type    | `Module` (instead of `Script`)                  |
| Module name        | `pytest`                                        |
| Parameters         | `tests/backend/test_database.py -v`             |
| Working directory  | The root of your Smart-Box checkout             |

Use your own local paths rather than copying another team member's absolute
paths. On macOS, the interpreter is normally `../../.venv/bin/python` inside the
project. On Windows, it is `.venv\Scripts\python.exe`.

The backend loads the root `../../.env` automatically; there is no need to select it
again in the run configuration. Existing environment variables take precedence
over values in `.env`.

Click **Apply**, then **Run**. Subsequent checks can use the same saved
configuration and the Run button, without entering terminal commands.

## Read the result

A successful run includes:

```text
test_database_connection PASSED
```
