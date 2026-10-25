# TEMSAFE database

We use **MySQL 8.4 or later**. [`schema.sql`](schema.sql) creates six tables for
boxes, users, access permissions, temperature profiles, measurements and reviews.
Choose either setup below.

## With Docker Compose

1. Start a Docker environment with Compose support. Docker Desktop is one option.
2. Copy [`.env.example`](../.env.example) to `.env` in the project root if you do
   not already have one. Set different passwords for `MYSQL_ROOT_PASSWORD` and
   `MYSQL_PASSWORD`.
3. From the project root, run:

```sh
docker compose up -d --wait mysql
```

On the first start, this creates the `temsafe` database, the `temsafe` database
user and all six tables. Connect using host `127.0.0.1`, port `3307` (unless changed
in `.env`), user `temsafe` and your `MYSQL_PASSWORD`.

To stop it, use `docker compose stop mysql`. Your data stays in the Docker volume.
Changing `.env` later does not change an existing database password. Avoid
`docker compose down -v` unless you want to delete the stored data.

## Without Docker

1. Install and start MySQL, or use a server you have access to.
2. Connect with an administrator account in your SQL client and run:

```sql
CREATE
DATABASE temsafe CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;
CREATE
USER 'temsafe'@'localhost' IDENTIFIED BY 'replace-with-your-own-password';
GRANT ALL PRIVILEGES ON temsafe.* TO
'temsafe'@'localhost';
```

This account is for local development. If the database or account already exists,
use the existing setup. For a remote server, ask its administrator for an account
that can connect from your computer.

3. Select the empty `temsafe` database in your SQL client, open
   [`schema.sql`](schema.sql) and execute the whole file once. Do not import it
   again over existing tables.
4. Create or update `.env` in the project root with your connection details:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=temsafe
MYSQL_USER=temsafe
MYSQL_PASSWORD=replace-with-your-own-password
```

Use your server's actual host and port. `MYSQL_ROOT_PASSWORD` is only needed for
our Docker setup. Keep `.env` out of Git.

## Add the prototype box

Database changes live in `database/migrations` as numbered SQL files. We apply
them manually in order; no extra migration tool is needed for this step.

1. Connect to your MySQL server in your SQL client and select `temsafe`.
2. After the tables exist, open and run
   [`001_add_prototype_box.sql`](migrations/001_add_prototype_box.sql).
3. Click **Commit** if auto-commit is off.

This adds `TS-01`, named `Prototype box TS-01`. Its `last_seen_at` is `NULL`
until the device contacts the server. Running this file again preserves an
existing box without creating a duplicate. If you already added TS-01, keep it.
These steps work with or without Docker; do not re-run `schema.sql`.

With the backend running, open
[`/api/boxes/TS-01`](http://127.0.0.1:8000/api/boxes/TS-01) to see the box through the API.

## Check it works

In your SQL client, select `temsafe` and run:

```sql
SHOW
TABLES;
```

You should see `app_users`, `box_access`, `boxes`, `sample_reviews`,
`temperature_samples` and `threshold_profiles`.

Then follow the short [backend test instructions](../tests/backend/README.md).
The tests check the connection and save a measurement, read it back and remove
their test records. They also check the reading endpoint. The expected result is **3 passed**.

The schema creates empty tables; the migration above adds the prototype box.
It does not add users, temperature profiles or measurements.
For the design and data rules, see the
[database research](../docs/research/database-research.md).
