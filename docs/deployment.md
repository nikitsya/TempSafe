# TempSafe deployment

TempSafe was deployed on 2 November 2026 at
[https://tempsafe.app](https://tempsafe.app).

## Hosting setup

| Component         | Configuration                                                                       |
|-------------------|-------------------------------------------------------------------------------------|
| Server            | AWS EC2, Ubuntu Server 24.04 LTS, x86-64, `t3.small`                                |
| Storage           | 20 GiB EBS volume                                                                   |
| DNS               | Cloudflare A record for `tempsafe.app` pointing to the server's public IPv4 address |
| HTTPS             | Caddy, with automatic certificate management                                        |
| Backend           | FastAPI and Uvicorn, managed by `tempsafe.service`                                  |
| Backend listener  | `127.0.0.1:8000`, reached through Caddy                                             |
| Database          | MySQL 8.4 in Docker Compose, with the persistent `mysql_data` volume                |
| Database listener | `127.0.0.1:3307` on the host                                                        |
| Project directory | `/home/ubuntu/Smart-Box`                                                            |

The frontend and API share the same domain. Closing an SSH session or a local SSH tunnel does not stop
the services. The EC2 instance must remain running for the site to be available.

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

See the [frontend guide](../frontend/README.md) for application limitations and the
[MQTT guide](mqtt.md) for worker deployment and device integration status.

Caddy Basic Authentication was used during initial setup. It is a separate server access control,
not application authentication. If it is removed, the API is publicly
accessible, including reading submission. Use test data only; implement authentication and authorisation
before handling real user or device data.

For connection diagrams, PyCharm tunnel settings and the distinction between
verified configuration and pending server checks, see [Database connections](database-connections.md).

## Service checks

Run these commands over SSH on the Ubuntu server:

```sh
sudo systemctl status tempsafe caddy --no-pager
cd /home/ubuntu/Smart-Box
sudo docker compose ps
curl --fail http://127.0.0.1:8000/api/health
```

The services should be active and the MySQL container healthy. The health endpoint returns
`{"status":"ok"}`, but does not test the database connection. The Compose health check separately
checks MySQL access and the presence of the `sample_reviews` table.

To inspect recent logs:

```sh
sudo journalctl -u tempsafe -n 50 --no-pager
sudo journalctl -u caddy -n 50 --no-pager
```

After changing `/etc/caddy/Caddyfile`, validate it before reloading:

```sh
sudo caddy validate --config /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

## Configuration and persistence

Database credentials are stored in the server's `.env` file. Keep that file, SSH private keys and
access credentials out of Git. The backend service definition is stored at
`/etc/systemd/system/tempsafe.service`; Caddy configuration is stored at `/etc/caddy/Caddyfile`.

The Docker volume preserves database data when containers are recreated. It is not a backup;
do not run `docker compose down -v` unless the stored data should be deleted.

The initial deployment uses an automatically assigned public IPv4 address. After stopping and starting
the EC2 instance, check its address and update the Cloudflare A record if it has changed.
An Elastic IP can provide a stable address if configured later.

Changes committed locally do not automatically update the server. Deploy application changes separately,
apply any required database migrations and restart `tempsafe.service` after updating the backend.

## Public endpoint hardening

On 5 November 2026, unauthenticated requests to the public `/docs`, `/redoc` and
`/openapi.json` endpoints returned 200. The three headers below were absent on the
checked responses. To apply the prepared change after review, install the
[site directives](../deploy/tempsafe-hardening.caddy) on EC2:

```sh
cd /home/ubuntu/Smart-Box
sudo install -m 644 deploy/tempsafe-hardening.caddy /etc/caddy/tempsafe-hardening.caddy
```

Add `import /etc/caddy/tempsafe-hardening.caddy` inside the existing
`tempsafe.app` site block. Keep the site's reverse proxy and any access controls.
Validate the complete Caddyfile and reload using the service commands above.
Check the public URLs from outside EC2:

```sh
for endpoint in docs redoc openapi.json api/health; do
    curl -sS -o /dev/null -D - "https://tempsafe.app/$endpoint"
done
```

Expect 404 for the three documentation paths and 200 for health. Check for
`Strict-Transport-Security` with `max-age=31536000`, `X-Content-Type-Options: nosniff`
and `X-Frame-Options: DENY` on the responses.

## Stored data checks

- **Credentials.** On 5 November 2026, the project's server-side `.env` belonged to
  `ubuntu:ubuntu` with mode `600`. Check ownership and permissions with
  `stat -c '%a %U:%G %n' /home/ubuntu/Smart-Box/.env` without printing its contents.
- **Application passwords.** The schema stores user password hashes in
  `app_users.password_hash`. The login implementation on the secure API branch uses
  Argon2id. Check the deployed revision before claiming login is live.
- **EBS encryption.** Verification is pending. In EC2, open the instance's Storage
  tab and inspect the **Encrypted** field for the EBS volume backing the MySQL
  Docker volume. Record the result for that volume. The account default alone
  cannot confirm encryption on an existing volume.
- **MQTT storage.** On 5 November the standalone MQTT service was active on EC2.
  MySQL held 155 samples for TS-01, most recently received at 00:00:10 UTC that day.
  For a fresh end-to-end check, match a new Pi sample ID to the worker's storage
  acknowledgement and the same ID in MySQL.
