# TEMSAFE database

The initial central database contains six InnoDB tables. Use MySQL 8.4 or later
with strict SQL mode enabled and foreign-key and CHECK enforcement left enabled.
SQLite remains the device's separate offline queue.

## Run with Docker Compose

Install and start Docker Desktop. From the repository root, prepare the local
configuration once:

```sh
cp -n .env.example .env
```

Set separate `MYSQL_ROOT_PASSWORD` and `MYSQL_PASSWORD` values in `.env` before
the first start. This file is ignored by Git. If `.env` already exists, add any
missing settings without replacing its existing contents.

Start the database and wait for the schema to become available:

```sh
docker compose up -d --wait mysql
docker compose ps
```

The official MySQL 8.4 image creates `temsafe`, a local development user named
`temsafe`, and all six tables automatically on the first start with an empty
volume. See the [official image documentation](https://hub.docker.com/_/mysql).
The health check verifies an authenticated connection and the final schema table.
The development user has full privileges within `temsafe`; it is not the
restricted runtime account described below.

Connect without installing MySQL on the host:

```sh
docker compose exec mysql mysql -u temsafe -p temsafe
```

Enter `MYSQL_PASSWORD` from `.env`, then run `SHOW TABLES;`. For MySQL Workbench
or a backend running on the host, use `127.0.0.1`, port `3307`, database `temsafe`
and user `temsafe`. This port avoids the usual local MySQL port `3306`; change
`MYSQL_PORT` in `.env` if needed. Administrative access inside the container uses
`docker compose exec mysql mysql -u root -p` and `MYSQL_ROOT_PASSWORD`.

Routine commands:

```sh
docker compose stop mysql
docker compose up -d --wait mysql
docker compose logs --tail=50 mysql
```

Data persists in the named volume across stops, restarts and `docker compose down`.
Do not use `docker compose down -v` unless you intend to delete the database.
The restart policy starts the container again when Docker starts, unless you
explicitly stopped it. Enable Docker Desktop startup at login if desired.

The image only imports the schema and sets credentials when the data volume is
empty. Editing `schema.sql` or passwords in `.env` does not update an existing
database; use migrations or an explicit password change instead.

## Initialise an empty database without Docker

From the repository root, using an account allowed to create databases and tables:

```sh
mysql -u root -p -e "CREATE DATABASE temsafe CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;"
mysql -u root -p temsafe < database/schema.sql
mysql -u root -p temsafe -e "SHOW TABLES;"
```

Add `--host` and `--port` if required by the local installation. Passwords are
prompted for; do not put them in source files or command arguments.

This baseline deliberately fails if its tables already exist. It does not drop,
replace or migrate existing data. MySQL DDL commits implicitly, so a failed import
can leave a partial installation: inspect it before retrying. Future changes to an
installed database require separate versioned migrations.

No users, credentials, boxes or temperature limits are seeded. The lower limit
has not yet been agreed. Provision a box, an Argon2id password hash, its access
assignment and an approved profile before ingesting samples. The backend health
endpoint still checks application liveness only; database integration is pending.

## Tables and review decisions

| Table                 | Purpose and integrity rules                                                                |
|-----------------------|--------------------------------------------------------------------------------------------|
| `boxes`               | Device identity, display name and nullable last authenticated contact time.                |
| `app_users`           | Unique local sign-in identifier and encoded password hash.                                 |
| `box_access`          | Many-to-many user/box assignments; duplicate assignments are rejected.                     |
| `threshold_profiles`  | Versioned limits with `lower_c < warning_c < upper_c`, source and demo flag.               |
| `temperature_samples` | Original sample identity, persistent device sequence, timing, quality and applied profile. |
| `sample_reviews`      | Latest review acknowledgement per sample, with reviewer and server timestamp.              |

The original relationships and field names are retained. Named constraints make
failures easier to diagnose. Explicit Unicode character settings remove dependence
on the server default; login identifiers are case-sensitive and accent-sensitive.
Box and UUID identifiers use case-sensitive ASCII comparison. The application
must validate identifier formats and consistently use canonical lower-case UUIDs.

The sample primary key and unique `(box_id, sequence_no)` prevent duplicate
storage. The composite profile foreign key prevents applying another box's profile.
The `(box_id, observed_at)` index supports history filters; the sequence index
supports retrieving the latest sample even when older data arrives later.
Valid readings require a value between -40 and 80°C; sensor errors require NULL.
Reliable clocks require an observation time; unreliable clocks require NULL.
These are recording rules, not medicine storage limits.

Deletion uses MySQL's default restrictive foreign-key behaviour. Delete dependent
review records explicitly before any agreed sample retention operation. Revoking
an access assignment does not remove the user's historical review attribution.

## Application responsibilities

- Set `time_zone = '+00:00'` on **every connection**; the schema sets it only for
  its own import session. DATETIME stores no time-zone information.
- Keep strict SQL mode enabled so invalid enum values and truncated data fail.
- Treat profiles and recorded samples as immutable. Use a restricted runtime
  account without UPDATE/DELETE privileges on those tables; use a separate
  maintenance account for agreed retention. The schema itself does not enforce
  immutability against privileged updates.
- Validate authenticated box identity and authorise every read and review.
  Foreign keys do not enforce user permissions or whether a sample is flagged.
- On a duplicate key, compare the original sample payload. Acknowledge identical
  retries only after commit and reject conflicting IDs or sequences; do not
  overwrite samples with `REPLACE` or an upsert.
- Order current state by persistent device sequence, including sensor errors.
  Retain observation time for history and check freshness independently of contact.
- Update `last_seen_at` from authenticated contact, not buffered observation time.
- Derive Normal, Warning and Alert from the recorded profile; invalid samples
  remain unknown. Unreliable-clock samples need a separate untimed history view.

Session storage/logout invalidation, device credential registration, Web Push
subscriptions, notification outbox/deduplication and maintenance tracking remain
follow-up implementation work. This initial structure does not claim to implement
those workflows or the API.

## Run integrity checks

Configure a MySQL login path without committing credentials:

```sh
mysql_config_editor set --login-path=temsafe-test --host=127.0.0.1 --user=root --password
python3 tests/database/check_schema.py --login-path=temsafe-test
```

The runner uses the installed `mysql` client and Python standard library. It creates
a uniquely named `temsafe_schema_test_*` database, imports the real schema, tests
valid data and rejected writes, then drops only that temporary database. The
account therefore needs CREATE/DROP privileges. Do not use `--force`, which would
mask SQL errors. Connection options such as `--socket` may also be passed.

Validation on 20 October 2026: all 18 database checks passed against an isolated
MySQL 9.4.0 instance; both existing backend smoke tests also passed. MySQL 8.4
was not available for a separate compatibility run.
