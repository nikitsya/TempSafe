# TempSafe deployment

TempSafe was first deployed on 2 November 2026 at
[https://tempsafe.app](https://tempsafe.app).

## Hosting setup

| Component         | Configuration                                                                       |
|-------------------|-------------------------------------------------------------------------------------|
| Server            | AWS EC2, Ubuntu Server 24.04 LTS, x86-64, `t3.small`                                |
| Storage           | 20 GiB EBS volume                                                                   |
| DNS               | Cloudflare A record for `tempsafe.app` pointing to the server's public IPv4 address |
| HTTPS             | Nginx with a Certbot-managed Let’s Encrypt certificate                              |
| Backend           | FastAPI and Uvicorn, managed by `tempsafe.service`                                  |
| Backend listener  | `127.0.0.1:8000`, reached through Nginx                                             |
| Database          | MySQL 8.4 in Docker Compose, with the persistent `mysql_data` volume                |
| Database listener | `127.0.0.1:3307` on the host                                                        |
| Project directory | `/home/ubuntu/Smart-Box`                                                            |

The frontend and API share the same domain. Closing an SSH session or a local SSH tunnel does not stop
the services. The EC2 instance must remain running for the site to be available.

## HTTPS on Ubuntu

The [Nginx site](../../deploy/tempsafe-nginx.conf) serves the public domain on 443.
It redirects HTTP to HTTPS and serves HTTP-01 certificate challenges for both
`tempsafe.app` and `mqtt.tempsafe.app` from `/var/www/letsencrypt`. Mosquitto
owns port 8883 and uses its own certificate and renewal hook.

On a new host, install Nginx and Certbot. Point the two public DNS names at EC2
and allow port 80. Create the webroot with `sudo install -d -m 755 /var/www/letsencrypt`.
Enable the port-80 server block from the site file on its own first, so that the
challenge path works before the HTTPS certificate exists. On an existing host,
serve that same challenge path through the running proxy until the certificate
has been issued. Preserve any existing proxy-level authentication during migration.
Then run:

```sh
sudo certbot certonly --webroot -w /var/www/letsencrypt --cert-name tempsafe.app -d tempsafe.app
sudo install -m 644 deploy/tempsafe-nginx.conf /etc/nginx/sites-available/tempsafe
sudo ln -sfn /etc/nginx/sites-available/tempsafe /etc/nginx/sites-enabled/tempsafe
sudo nginx -t
```

Disable the distribution’s default site if enabled. When replacing another proxy,
stop it only after validation, start Nginx and check the responses below. If the
checks fail, stop Nginx and restart the previous service. After successful checks,
enable Nginx at boot and disable the previous service. For an existing Nginx
instance, reload it after validation.

```sh
sudo install -m 755 deploy/tempsafe-nginx-renew /etc/letsencrypt/renewal-hooks/deploy/tempsafe-nginx
sudo systemctl enable --now certbot.timer
sudo certbot renew --dry-run
curl -I http://tempsafe.app/
curl -i https://tempsafe.app/api/health
curl -I https://tempsafe.app/docs
```

Expect a 308 redirect to HTTPS, a 200 health response and a 404 for the
documentation paths (`/docs`, `/redoc` and `/openapi.json`). HTTPS responses
carry HSTS, `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
The renewal hook reloads Nginx after renewal of the website certificate.

### Deployment verification on 5 November 2026

External checks returned 200 for the home page and `/api/health`, 308 for the
HTTP redirect and 404 for `/docs`, `/redoc` and `/openapi.json`. The health
response identified Nginx and carried all three security headers. The box’s latest
reading still returned 200 without a session on the deployed revision. Confirm
per-box authorisation when deploying the protected API. This records the old revision;
the checks below describe the deployed session-based API.

On EC2, Nginx listened on ports 80 and 443 and Mosquitto listened on 8883.
Certbot successfully simulated renewal for both domains. The website renewal
hook passed its configuration test and reloaded Nginx.

## Current deployment — verified 21 November 2026

The server runs commit `cf815389eb916f02fca2b9485e1f2a7590fe3104` from
[PR #33](https://github.com/nikitsya/TempSafe/pull/33), which adds dual-sensor
ingestion and sensor-filtered API queries. It replaced `20b67cd` at approximately
17:52 UTC. The checkout at `/home/ubuntu/Smart-Box` remains detached at the selected
commit; future merges do not deploy automatically.

Migration 007 was applied to the existing `temsafe` MySQL database before the
backend update. It added `sensor_location` and both sensor-filtered indexes.
All 11,189 existing samples became `inside`. A comparison of every original
sample field before and after migration confirmed that values, identifiers,
timestamps and numbering were preserved. The selected box profiles also remained
unchanged. The backend was stopped briefly for migration and restarted afterwards.

The dependencies, service configuration, broker ACLs, credentials, database name
and Docker volume were retained. The existing editable installation loads the
updated checkout without a dependency reinstall. Frontend files were unchanged
between the two commits and their file hashes matched after deployment.

Verification completed at 17:54 UTC confirmed:

- `tempsafe`, `nginx` and `mosquitto` are active; the server checkout is clean.
- Public HTTPS health returns `200`. Anonymous readings and configuration
  requests return `401`.
- Authenticated latest-reading requests default to `inside` and match an explicit
  `sensor_location=inside` request. Inside history returns inside samples only.
- No outside samples were present. Outside history returns `200` with an empty
  list, and outside latest returns `404`; it does not substitute an inside sample.
  An invalid sensor location returns `422`.
- The configuration API still returns the selected database profile. The temporary
  verification session was revoked and its removal was checked.
- A uniquely identified diagnostic MQTT client authenticated over verified TLS
  and subscribed to the readings topic with QoS 1. The deployed backend also had
  an established broker connection. Existing device/backend permissions for
  readings, acknowledgements and configuration were verified without changing them.

No synthetic measurements were published or added to production. Fresh physical
Pi readings, their matching storage acknowledgements and outside response values
still require a coordinated device check. The frontend owner must handle shared
sequence gaps before permanent outside collection is enabled; see the
[dual-sensor handover](dual-sensor-rollout.md#frontend-handover).

The private backup directory is
`/home/ubuntu/tempsafe-deploy-backups/20261121T174946Z-dual-sensor`.
It contains a completed SQL dump and checksum, the previous commit and package
list, configuration backups, frontend hashes, migration comparisons and
`dual-sensor-verification.json`. The deployment and verification scripts are also
retained there. The directory is private; restoration and an off-server copy were
not tested during this deployment.

## Configuration delivery deployment — verified 21 November 2026

The preceding deployment used commit `20b67cd551b6676e5af18b87ff4005f9ec042322` from
[PR #32](https://github.com/nikitsya/TempSafe/pull/32), which adds retained MQTT
configuration delivery. The previous deployed revision was `3eb7a1c`. The checkout
at `/home/ubuntu/Smart-Box` is detached at the selected commit and does not follow
new GitHub commits automatically.

The installed FastMQTT 2.2.0 and gmqtt 0.8.0 versions matched the local test
environment. No dependency upgrade or database migration was needed. The service
continues to use one Uvicorn worker and the existing `temsafe` database and credentials.

The broker ACL now grants `device-TS-01` read access and `backend-ingest` write
access to `tempsafe/boxes/TS-01/configuration`. Existing readings and acknowledgement
permissions were preserved. Mosquitto was reloaded before the backend was restarted.

Verification after deployment confirmed:

- `tempsafe`, `mosquitto` and `nginx` are active, and the server checkout is clean.
- HTTPS `/api/health` returns `200` with `{"status":"ok"}`. Anonymous latest-reading
  and configuration requests return `401`.
- A uniquely identified diagnostic MQTT client connected over verified TLS and
  received the retained configuration with QoS 1. Its complete payload matched
  the selected MySQL profile: `e93a4368-e11a-4f27-8b31-d55d61392548`, with limits
  `0.00`, `24.00` and `25.00` degrees Celsius.
- The subscribed client then received a live repeat of the same configuration.
  No configuration-publication failures appeared in the backend journal during
  the checks.
- Temporary read access granted to the backend account for this diagnostic check
  was removed afterwards; the final ACL contains only the intended permissions.

The existing limits were not changed. This verifies backend-to-broker publication,
not adoption on the physical Raspberry Pi. Deploy the compatible device scripts
and verify the saved profile, new sample profile IDs and LED/buzzer behaviour with
the device operator. Second-sensor ingestion is not part of this deployment.

The private backup directory is
`/home/ubuntu/tempsafe-deploy-backups/20261121T153549Z-configuration-sync`.
It contains a non-empty SQL dump, the previous commit and installed package list,
the previous broker ACL/configuration, service configuration and environment
files. `configuration-verification.json` records the retained and live-repeat
checks. Keep these files private; the directory and SQL dump use modes `700` and
`600` respectively. Restore testing was not performed during this rollout.

## Deployment verification on 8 November 2026

At this earlier check, the server ran commit
`3578cfe77c6738fe2e08366337ec8de4776a58ad`, deployed on 7 November with sign-in
integration from PR #25. The following observations describe that revision.

- `tempsafe`, `nginx` and `mosquitto` are active; the MySQL container is healthy.
- FastMQTT runs inside FastAPI with one Uvicorn worker. The previous
  `tempsafe-mqtt.service` was stopped and disabled during the update.
- `box_configuration` and `user_sessions` exist.
- External HTTPS checks returned 200 for the home page and `/api/health`, 401
  for anonymous latest-reading and history requests,
  and 404 for `/docs`.

Sign-in and sign-out are deployed. Application accounts are provisioned separately
from MySQL accounts and require a box assignment. Passwords are stored as Argon2id
hashes. The checks above confirm anonymous access is rejected; they do not replace
an authenticated browser check with an assigned account.

The deployment logs confirmed an MQTT broker connection. A fresh Pi-to-MySQL
reading and matching storage acknowledgement still need verification.

## Network access

The saved EC2 inbound rules supplied on 3 November 2026 allow:

| Port           | Source                                 | Purpose                                                   |
|----------------|----------------------------------------|-----------------------------------------------------------|
| TCP 80 and 443 | `0.0.0.0/0`                            | HTTP and HTTPS for the website                            |
| TCP 8883       | `0.0.0.0/0`                            | Authenticated MQTT over TLS from changing device networks |
| TCP 22         | Operator's public IPv4 address (`/32`) | SSH administration                                        |

No inbound rules expose MQTT port 1883 or MySQL ports 3306/3307. The supplied instance view shows no
broad All TCP or All traffic rule. Broker accounts, TLS and topic permissions are documented in the
[MQTT guide](mqtt.md); AWS network rules do not replace those controls.

## Current limitations

See the [frontend guide](../../frontend/README.md) for application limitations and the
[MQTT guide](mqtt.md) for FastMQTT deployment and device integration status.

Nginx terminates TLS and forwards requests to Uvicorn. FastAPI uses browser sessions
to control access to each box and separate credentials for HTTP device submissions.
For a new installation, install the dependencies, create the current schema and
provision a user with access to the prototype box. For an existing database, check
which migrations are missing before applying them. Verify that anonymous requests
are rejected and that the assigned user can read the box’s data.
See the [authentication and setup guide](../api/api-contract.md#authentication).

For connection diagrams, PyCharm tunnel settings and the distinction between
verified configuration and pending server checks, see [Database connections](database-connections.md).

## Service checks

Run these commands over SSH on the Ubuntu server:

```sh
sudo systemctl status tempsafe nginx mosquitto --no-pager
cd /home/ubuntu/Smart-Box
sudo docker compose -p temsafe ps
curl --fail http://127.0.0.1:8000/api/health
```

The services should be active and the MySQL container healthy. The health endpoint returns
`{"status":"ok"}`, but does not test the database connection. The Compose health check separately
checks MySQL access and the presence of the `sample_reviews` table. It does not
verify that all application migrations have been applied.

To inspect recent logs:

```sh
sudo journalctl -u tempsafe -n 50 --no-pager
sudo journalctl -u nginx -n 50 --no-pager
```

After changing `/etc/nginx/sites-available/tempsafe`, validate it before reloading:

```sh
sudo nginx -t && sudo systemctl reload nginx
```

## Configuration and persistence

Database credentials are stored in the server's `.env` file. Keep that file, SSH private keys and
access credentials out of Git. The backend service definition is stored at
`/etc/systemd/system/tempsafe.service`, with the MQTT override at
`/etc/systemd/system/tempsafe.service.d/mqtt.conf`. The service also reads
`/etc/tempsafe/mqtt.env`; the override enables MQTT and selects one Uvicorn worker.
The Nginx site is enabled through `/etc/nginx/sites-enabled/tempsafe`.

The Docker volume preserves database data when containers are recreated. It is not a backup;
do not run `docker compose down -v` unless the stored data should be deleted.

The initial deployment uses an automatically assigned public IPv4 address. After stopping and starting
the EC2 instance, check its address and update the Cloudflare A record if it has changed.
An Elastic IP can provide a stable address if configured later.

## Updating the application

Changes committed locally or pushed to GitHub do not automatically update the server.
For each deployment:

1. Check the server working tree and record its current commit. Select the reviewed
   target commit explicitly; do not assume the detached checkout follows `master`.
2. Back up the database and any configuration files that will change. Keep the
   previous commit available for rollback.
3. Review the target's dependencies and migrations. Existing installations need
   migrations 003 and 004 where their tables are absent, and migration 007 before
   deploying dual-sensor ingestion if `sensor_location` is absent.
   Check migrations 008 and 009 for applied-profile confirmations and Web Push,
   then update the runtime grants to match the upgraded schema. See the
   [database guide](../../database/README.md#device-confirmation-and-web-push-migrations).
4. Deploy the selected code and install changed dependencies with
   `.venv/bin/python -m pip install -e .`. Preserve `.env`, MQTT credentials and
   the Compose project name `temsafe`, which selects the existing database volume.
5. Restart `tempsafe.service` and check the services, logs, HTTPS responses and
   authenticated access. Check MQTT storage separately with a real device reading.

If application checks fail, restore the previous code and restart the service.
Confirm that it is compatible with any applied migration before rollback; switching
commits does not undo database changes. Do not automatically restore an old database
snapshot over readings received since the backup.

## Deployment backups

The two updates on 7 November created restricted backup directories on the server:

- `/home/ubuntu/tempsafe-deploy-backups/20261107T232839Z`
- `/home/ubuntu/tempsafe-deploy-backups/20261107T235655Z`

Each contains a database SQL dump and the previous revision. The first also contains
copies of the service definition and MQTT environment file. These are manual backups
on the same server. On 25 November, an encrypted off-server backup was restored
and checked in isolation. See the [recovery drill](database-recovery.md) for the
recorded counts, access checks and recovery time. A recurring backup schedule
remains unverified. Keep dumps and configuration copies private.

## Stored data checks

- **Credentials.** On 5 November 2026, the project's server-side `.env` belonged to
  `ubuntu:ubuntu` with mode `600`. Check ownership and permissions with
  `stat -c '%a %U:%G %n' /home/ubuntu/Smart-Box/.env` without printing its contents.
- **Application passwords.** The schema stores user password hashes in
  `app_users.password_hash`. The deployed login implementation uses Argon2id;
  credentials are not stored as plaintext application passwords.
- **EBS encryption.** On 6 November 2026, a check on the EC2 host traced the
  MySQL container's data directory to the root EBS volume, `vol-00d71e3f3b6db9d09`.
  The EC2 console showed **Encrypted** for this 20 GiB volume with the KMS key
  alias `aws/ebs`. This confirms encryption at rest for MySQL data on that disk.

  ![EC2 volume details showing the encryption status as Encrypted](../assets/operations/ebs-volume-encryption.png)
- **MQTT storage.** On 5 November the standalone MQTT service was active on EC2.
  MySQL held 155 samples for TS-01, most recently received at 00:00:10 UTC that day.
  That was the previous ingestion service. FastMQTT replaced it on 7 November.
  For a fresh end-to-end check, match a new Pi sample ID to FastMQTT's storage
  acknowledgement and the same ID in MySQL.

## Package name update: tempsafe

The Python package is now `tempsafe`, and its distribution is `tempsafe-backend`.
After deploying this change, reinstall with `.venv/bin/python -m pip install -e .`
and update every Uvicorn service command (including the MQTT override) to
`tempsafe.main:app`. Run `sudo systemctl daemon-reload` before restarting the
service. The 8 November deployment predates this package rename; the 21 November
verification confirmed that the service already uses `tempsafe.main:app`.

New project settings use the `TEMPSAFE_` prefix. Existing `TEMSAFE_` settings
remain accepted as a compatibility fallback; an explicitly set new setting takes
precedence, including an empty value. Rename the keys in private environment files
when updating an installation, preserving their values.

New installations default to MySQL database and user `tempsafe`. Existing databases
are not renamed by this code change. On the recorded EC2 installation, retain
`MYSQL_DATABASE=temsafe`, `MYSQL_USER=temsafe` and the Compose project name
`temsafe` to keep using the existing data and volume. Set these explicitly before
running Compose or starting the renamed backend. Changing a default does not
migrate a database, rename a MySQL account or copy a Docker volume.
