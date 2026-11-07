# TempSafe database

We use **MySQL 8.4 or later**. [`schema.sql`](schema.sql) creates eight tables for
boxes, users, access permissions, temperature profiles, measurements, reviews, the selected box configuration and user
sessions.
Choose either setup below.

## Table relationships

See [Figure 1: the database ERD](../docs/design/database-erd.md#figure-1-tables-keys-and-relationships)
for the relationships between boxes, users, profiles, measurements and reviews.
The document also explains composite constraints and historical threshold profiles.

## Hosted database access

See [Database connections](../docs/operations/database-connections.md) for the backend connection,
PyCharm SSH tunnel, credentials, network boundaries and backup verification status.

## With Docker Compose

1. Start a Docker environment with Compose support. Docker Desktop is one option.
2. Copy [`.env.example`](../.env.example) to `.env` in the project root if you do
   not already have one. Set different passwords for `MYSQL_ROOT_PASSWORD` and
   `MYSQL_PASSWORD`.
3. From the project root, run:

```sh
docker compose up -d --wait mysql
```

With the default project name, Docker Desktop shows the container as
`tempsafe-mysql-1` and stores its data in `tempsafe_mysql_data`.

On the first start, this creates the `temsafe` database, the `temsafe` database
user and all eight tables. Connect using host `127.0.0.1`, port `3307` (unless changed
in `.env`), user `temsafe` and your `MYSQL_PASSWORD`.

To stop it, use `docker compose stop mysql`. Your data stays in the Docker volume.
Changing `.env` later does not change an existing database password. Avoid
`docker compose down -v` unless you want to delete the stored data.

## Without Docker

1. Install and start MySQL, or use a server you have access to.
2. Connect with an administrator account in your SQL client and run:

```sql
CREATE DATABASE temsafe CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;
CREATE USER 'temsafe'@'localhost' IDENTIFIED BY 'replace-with-your-own-password';
GRANT ALL PRIVILEGES ON temsafe.* TO 'temsafe'@'localhost';
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

## Apply migrations

For either setup, select `temsafe` in your SQL client after the tables exist.
Run these files manually in order, then commit if auto-commit is off:

| File                                                                                              | Result                                                                                                  |
|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| [001_add_prototype_box.sql](migrations/001_add_prototype_box.sql)                                 | Adds `TS-01`, named `Prototype box TS-01`, with no recorded device contact.                             |
| [002_add_prototype_temperature_profile.sql](migrations/002_add_prototype_temperature_profile.sql) | Adds its demo profile: lower threshold `0.00°C`, warning threshold `24.00°C` and upper limit `25.00°C`. |

The profile ID is `e93a4368-e11a-4f27-8b31-d55d61392548`. These migrations preserve
existing records when run again; do not re-run `schema.sql`. They do not add users
or measurements. Future threshold changes require a new profile ID to preserve
historical settings.

See the [API contract](../docs/api/api-contract.md#temperature-classification)
for temperature classification rules.

## Threshold configuration migration

For an existing database, apply
[003_add_box_configuration.sql](migrations/003_add_box_configuration.sql) once after
backing up. Fresh databases created with the updated schema already have this table;
do not run migration 003 again. See the
[operator API guide](../docs/api/threshold-configuration.md) for selection and access rules.

## User session migration

On an existing database, check `SHOW TABLES;` for `user_sessions`. If the table
is missing, back up the database and run
[004_add_user_sessions.sql](migrations/004_add_user_sessions.sql) once.
The sign-in endpoint uses this table to create and expire sessions. Fresh databases
created with the current schema already include it.

## Heartbeat interval migration

Before starting the updated backend against an existing database, back it up and
apply [005_add_box_heartbeat_interval.sql](migrations/005_add_box_heartbeat_interval.sql)
once if `boxes.heartbeat_interval_seconds` is missing. Existing boxes receive the
60-second default. The current baseline already defines this column for fresh installs.

## Verify the setup

Select `temsafe` and run:

```sql
SHOW TABLES;
```

Expected tables: `app_users`, `box_access`, `boxes`, `sample_reviews`,
`temperature_samples`, `threshold_profiles`, `box_configuration` and `user_sessions`.

Follow the [backend test instructions](../tests/backend/README.md) to check database
access and API behaviour. For the schema rationale, see the
[database research](../docs/research/database-research.md).
