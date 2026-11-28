# TempSafe database

We use **MySQL 8.4 or later**. [`schema.sql`](schema.sql) creates eleven tables for
boxes, accounts, readings, threshold profiles, configuration and Web Push delivery.
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

On the first start, this creates the `tempsafe` database, the `tempsafe` database
user and all eleven tables. Connect using host `127.0.0.1`, port `3307` (unless changed
in `.env`), user `tempsafe` and your `MYSQL_PASSWORD`.

To stop it, use `docker compose stop mysql`. Your data stays in the Docker volume.
Changing `.env` later does not change an existing database password. Avoid
`docker compose down -v` unless you want to delete the stored data.

## Without Docker

1. Install and start MySQL, or use a server you have access to.
2. Connect with an administrator account in your SQL client and run:

```sql
CREATE DATABASE tempsafe CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;
CREATE USER 'tempsafe'@'localhost' IDENTIFIED BY 'replace-with-your-own-password';
GRANT ALL PRIVILEGES ON tempsafe.* TO 'tempsafe'@'localhost';
```

This account is for local development. If the database or account already exists,
use the existing setup. For a remote server, ask its administrator for an account
that can connect from your computer.

3. Select the empty `tempsafe` database in your SQL client, open
   [`schema.sql`](schema.sql) and execute the whole file once. Do not import it
   again over existing tables.
4. Create or update `.env` in the project root with your connection details:

```dotenv
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=tempsafe
MYSQL_USER=tempsafe
MYSQL_PASSWORD=replace-with-your-own-password
```

Use your server's actual host and port. `MYSQL_ROOT_PASSWORD` is only needed for
our Docker setup. Keep `.env` out of Git.

## Apply migrations

### Seed the prototype box and profile

For a database created with the base Compose file or the manual setup, select
`tempsafe` in your SQL client. Run the two seed files in order and commit if
auto-commit is off. The full local Compose setup runs them automatically on
the first start of a fresh volume.

| File                                                                                              | Result                                                                                                  |
|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| [001_add_prototype_box.sql](migrations/001_add_prototype_box.sql)                                 | Adds `TS-01`, named `Prototype box TS-01`.                                                              |
| [002_add_prototype_temperature_profile.sql](migrations/002_add_prototype_temperature_profile.sql) | Adds its demo profile: lower threshold `0.00°C`, warning threshold `24.00°C` and upper limit `25.00°C`. |

The demo profile ID is `e93a4368-e11a-4f27-8b31-d55d61392548`. Rerunning these
seed files preserves existing records. On a fresh installation, the first settings
save selects a desired profile. Accounts and measurements are added separately. Future threshold changes require a new profile ID to preserve
historical settings.

See the [API contract](../docs/api/api-contract.md#temperature-classification)
for temperature classification rules.

## Threshold configuration migration

If an existing database lacks `box_configuration`, back it up and apply
[003_add_box_configuration.sql](migrations/003_add_box_configuration.sql) once. Fresh databases created with the updated schema already have this table;
do not run migration 003 again. See the
[operator API guide](../docs/api/threshold-configuration.md) for selection and access rules.

## User session migration

On an existing database, check `SHOW TABLES;` for `user_sessions`. If the table
is missing, back up the database and run
[004_add_user_sessions.sql](migrations/004_add_user_sessions.sql) once.
The sign-in endpoint uses this table to create and expire sessions. Fresh databases
created with the current schema already include it.

## Upgrade existing box records

After deploying the updated backend, back up the database and
run [migration 006](migrations/006_remove_box_contact_settings.sql) with the project database selected. It removes
obsolete box contact columns where present. Fresh installations use the current baseline.

## Sensor location migration

For an existing database, back up and check
`SHOW COLUMNS FROM temperature_samples LIKE 'sensor_location';`.
If absent, apply [007_add_sensor_location.sql](migrations/007_add_sensor_location.sql)
once **before** deploying the updated backend. It adds `inside`/`outside` and indexes
for separate histories; existing rows become `inside`. Fresh databases created
from the current baseline already include these changes: do not run 007 again.
The unique `(box_id, sequence_no)` key remains shared by both sensors.
See the [dual-sensor rollout](../docs/operations/dual-sensor-rollout.md).

## Device confirmation and Web Push migrations

On an existing installation, take a backup and inspect the schema before deploying
the corresponding backend. If `box_configuration.applied_profile_id` is absent,
apply [migration 008](migrations/008_add_applied_profile.sql). Existing selections
start with no device confirmation.

[Migration 009](migrations/009_add_web_push.sql) creates `push_subscriptions`,
`push_box_state` and `push_deliveries`. Apply it if all three tables are absent.
If only some exist, compare them with the baseline before resuming the upgrade.
Both changes are already present in a fresh baseline. For the hosted schema,
apply the updated [runtime grants](operations/runtime-grants.sql) after the schema upgrade.

## Verify the setup

Select `tempsafe` and run:

```sql
SHOW TABLES;
```

A fresh database contains `app_users`, `box_access`, `box_configuration`, `boxes`,
`push_box_state`, `push_deliveries`, `push_subscriptions`, `sample_reviews`,
`temperature_samples`, `threshold_profiles` and `user_sessions`.

Follow the [backend test instructions](../tests/backend/README.md) to check database
access and API behaviour. For the schema rationale, see the
[database research](../docs/research/database-research.md).

## Existing installations with the old name

The defaults above apply to new installations. An existing database or account
named `temsafe` remains valid: set `MYSQL_DATABASE=temsafe` and `MYSQL_USER=temsafe`
explicitly in its private environment file. Keep its existing Compose project
name and volume. See the [package update](../docs/operations/deployment.md#package-name-update-tempsafe)
for the application rename; do not reinitialise a populated database.
