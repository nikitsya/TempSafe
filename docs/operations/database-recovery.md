# TempSafe database recovery

## Evidence for Scrumwise item 71824

On 25 November 2026 the hosted FastAPI service was switched to
`tempsafe_runtime` on the `temsafe` database. The previous schema-management
account remains separate. The service reads its runtime credentials from
`/etc/tempsafe/runtime-database.env` (root only). The systemd override
`zzzz-runtime-database.conf` removes the MySQL root password from the
service environment and masks the project's administrative `.env` file.

| Check                      | Observed result                                                                                                                                                                                                                                                            |
|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Effective grants           | Hosted `SHOW GRANTS` returned global `USAGE` and the seven table grants recorded in Git revision `0f302d9`.                                                                                                                                                                |
| Live service               | After restart, the local health endpoint returned 200. A connection using the running service's environment returned `tempsafe_runtime@%`, read the samples and locked a box row.                                                                                          |
| Backup                     | Consistent MySQL 8.4 dump from EC2. All eight base tables used InnoDB. The encrypted archive and separate key on the operator's Mac were both mode 0600.                                                                                                                   |
| Restore                    | Authenticated decryption and SQL import into an empty schema on a socket-only MySQL 9.4 instance took 0.175 seconds. This measures import, excluding setup and verification.                                                                                               |
| Data                       | 913 samples, 913 distinct sample IDs and 913 matching (profile ID, box ID) pairs. Two user-to-box assignments. Ordered INSERT statements for all restored tables matched the backup by SHA-256.                                                                            |
| User access                | Using FastAPI and the restricted account, sign-in returned 204, assigned-box readings 200, a real unassigned box 404, sign-out 204 and subsequent access 401. A temporary password and unassigned box were created only in the disposable copy, after the data comparison. |
| Runtime writes and denials | Creating a profile, selecting it and inserting and reading a sample succeeded in a rolled-back test transaction. MySQL denied CREATE TABLE with error 1142.                                                                                                                |

Archive SHA-256: `61ef0e8e0046429ad1621201ee3fff1e0cbcd5b3cae36f98c4733a50efd7ed6b`.
Ordered data SHA-256: `750cafa4cc4662c07ae6d305b2fb82bf0758689298c3b4cb5d059ad13b608d3a`.

## Create and retrieve the backup

Run from the repository on the authorised Mac with the project Python
environment (including cryptography), OpenSSH and MySQL client tools.
Use the EC2 SSH identity and verify its host key. The remote administrator
needs Docker access and the container's MySQL administrative credentials.
Keep schema changes paused for the duration of the single-transaction dump.
The sealing helper reads this small database into memory.

~~~sh
set -e -o pipefail
umask 077
key="$HOME/.tempsafe-recovery/recovery.key"
archive="$HOME/TempSafe-backups/production-$(date -u +%Y%m%dT%H%M%SZ).sql.fernet"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -i ~/.ssh/tempsafe-key.pem ubuntu@13.53.169.96 \
  'sudo -n docker exec temsafe-mysql-1 sh -c '\''MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump -uroot --single-transaction --quick --no-tablespaces --set-gtid-purged=OFF --skip-extended-insert --order-by-primary --hex-blob --routines --events --triggers "$MYSQL_DATABASE"'\''' \
  | .venv/bin/python database/operations/protected_dump.py seal "$key" "$archive"
shasum -a 256 "$archive"
~~~

Retrieve the recorded archive from `~/TempSafe-backups/production-20261125.sql.fernet`
on that Mac and verify its checksum above. Decryption requires the matching
key in `~/.tempsafe-recovery/recovery.key`. Losing the Mac and key together
would prevent recovery from this copy. Keep a separate protected copy of the
key in the team's approved credential store before relying on it for disaster
recovery. Attach only this report to Scrumwise.

## Restore and verify

Use a **fresh private instance**. The dump includes users, password hashes and
sessions. On the Mac initialise a new instance without TCP or MySQL X Protocol.
Keep its socket, logs and data inside the owner-only temporary directory.

~~~sh
set -e -o pipefail
umask 077
work=$(mktemp -d /private/tmp/tempsafe-drill.XXXXXXXX)
mysqld --no-defaults --initialize-insecure --datadir="$work/db" --log-error="$work/setup.log"
mysqld --no-defaults --daemonize --skip-networking --mysqlx=OFF \
  --datadir="$work/db" --socket="$work/mysql.sock" --pid-file="$work/mysql.pid" --log-error="$work/server.log"
key="$HOME/.tempsafe-recovery/recovery.key"
archive="$HOME/TempSafe-backups/production-20261125.sql.fernet"
mysql --no-defaults -uroot -S "$work/mysql.sock" -e 'CREATE DATABASE temsafe'
time ( .venv/bin/python database/operations/protected_dump.py open "$key" "$archive" \
  | mysql --no-defaults -uroot -S "$work/mysql.sock" temsafe )
~~~

Before changing any restored row, compare the two digests. An exact match
checks sample identifiers, profile contents, assignments and session records
from the same snapshot, even if production has since received more readings.

~~~sh
.venv/bin/python database/operations/protected_dump.py open "$key" "$archive" \
  | LC_ALL=C rg '^INSERT INTO ' | shasum -a 256
mysqldump --no-defaults -uroot -S "$work/mysql.sock" --no-create-info --skip-extended-insert \
  --order-by-primary --hex-blob --no-tablespaces temsafe | LC_ALL=C rg '^INSERT INTO ' | shasum -a 256
mysql --no-defaults -uroot -S "$work/mysql.sock" temsafe -e \
  'SELECT COUNT(*) AS samples, COUNT(DISTINCT s.sample_id) AS unique_ids,
          COUNT(p.profile_id) AS linked FROM temperature_samples s
   LEFT JOIN threshold_profiles p ON p.profile_id=s.profile_id AND p.box_id=s.box_id'
~~~

Only in the socket-only disposable instance, create the test runtime account
and run the access check. For the eight-table archive above, use the grants
from the drill revision. Later grants refer to columns and tables added after
that backup. For a newer backup, use the grants matching its schema. The check
changes one restored account's password and adds an unassigned box. Shut down the disposable instance and remove its
private
directory, including its plaintext data, after collecting the results.

~~~sh
mysql --no-defaults -uroot -S "$work/mysql.sock" -e "CREATE USER 'tempsafe_runtime'@'%'"
git show 0f302d9:database/operations/runtime-grants.sql | mysql --no-defaults -uroot -S "$work/mysql.sock"
.venv/bin/python database/operations/check_restored_access.py "$work/mysql.sock"
mysqladmin --no-defaults -uroot -S "$work/mysql.sock" shutdown
~~~

For a service rollback, remove only the runtime database systemd override,
run `sudo systemctl daemon-reload` and restart `tempsafe.service`. Verify
the health endpoint and database identity before retiring any account.
