# Smart Box: Database Technology Research

**Updated:** 4 October 2026.

**Scope:** one internal temperature sensor, a single-colour warning LED and Must Have phone notifications for a
paramedic medication box. The buzzer is Should Have; humidity reporting is outside this release.

The device records temperature inside a portable medication box. MySQL is the proposed central database; SQLite provides
a durable offline queue on the Raspberry Pi.

The baseline uses one internal sensor. An external temperature sensor is a possible future research extension and
is not included in this schema.

## 1. System technologies and languages

| Component              | Proposed technology              | Language or format       | Role in Smart Box                                                   |
|------------------------|----------------------------------|--------------------------|---------------------------------------------------------------------|
| Device application     | Raspberry Pi application         | Python                   | Read one internal temperature sensor; timestamp and queue samples   |
| Device's local storage | SQLite                           | SQL through Python       | Keep an offline upload queue on the device                          |
| Network messages       | HTTPS API                        | JSON payloads            | Transfer observations to the backend                                |
| Backend                | FastAPI                          | Python                   | Authenticate devices and users, validate messages and retrieve data |
| Database connector     | MySQL Connector/Python           | Python                   | Let the backend execute parameterised MySQL queries                 |
| Central database       | MySQL with InnoDB                | SQL                      | Store boxes, access permissions and historical observations         |
| User interface         | Web application                  | HTML, CSS and JavaScript | Display temperature, freshness, history and warnings                |
| Scheduled processing   | cron running application scripts | cron syntax and Python   | Produce summaries, check stale devices and perform maintenance      |

## 2. Data requirements

| Data                   | Example fields                                                            | Proposed policy                                                    | Purpose                                             |
|------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------|-----------------------------------------------------|
| Box metadata           | Box ID, name, last contact                                                | Provisioned once; contact updated on authenticated device requests | Identify the monitored box and connection freshness |
| Temperature samples    | Sample ID, sequence number, temperature Celsius, quality                  | Every 30 seconds, including explicit failed sample attempts        | Current state and history                           |
| Timing                 | Observed-at UTC, received-at UTC, clock reliability                       | Every sample; preserve original values on retry                    | Distinguish historical uploads and uncertain timing |
| Threshold profiles     | Profile ID, lower/upper limits, warning threshold, source note, demo flag | Immutable version for each configuration change                    | Reproduce the interpretation applied when recorded  |
| User access            | User ID and permitted box IDs                                             | On provisioning/change                                             | Enforce authorisation                               |
| Review acknowledgement | Sample ID, reviewer, reviewed-at                                          | Optional Should Have workflow                                      | Record review without altering measurements         |

Heartbeats are sent every 60 seconds. Proposed contact timeout is 3 minutes. The
device needs at least 24 hours of local queue capacity (2,880 sample attempts).

## 3. Database categories

| Category                  | Examples                   | Data model                                         | Smart Box relevance                                                                   |
|---------------------------|----------------------------|----------------------------------------------------|---------------------------------------------------------------------------------------|
| Relational                | MySQL, PostgreSQL, SQLite  | Tables linked by keys                              | Natural fit for boxes, users, permissions, threshold profiles and timestamped samples |
| Document                  | MongoDB, Cloud Firestore   | Collections of structured documents                | Useful when sensor payloads vary significantly                                        |
| JSON tree                 | Firebase Realtime Database | Hierarchical JSON                                  | Convenient for synchronising a small current-state view                               |
| Time-series               | InfluxDB                   | Timestamped measurements                           | Useful if high-volume sensor analytics becomes the main requirement                   |
| Key-value/data structures | Redis                      | Values and specialised structures accessed by keys | Possible cache or transient state store                                               |
| Graph                     | Neo4j                      | Nodes and relationships                            | Useful for relationship traversal; not a core need here                               |

## 4. Main comparison: MySQL, MongoDB and Firebase

| Criterion                 | MySQL / InnoDB                               | MongoDB                                                           | Cloud Firestore                                                      | Firebase Realtime Database                                                    |
|---------------------------|----------------------------------------------|-------------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Model                     | Relational tables                            | BSON documents                                                    | Collections and documents                                            | JSON tree                                                                     |
| Example design            | `boxes`, `temperature_samples`, `box_access` | Box and temperature-sample collections                            | Box documents with sample subcollections                             | Separate box-state and history paths                                          |
| Relationships             | Foreign keys and SQL joins                   | References or embedding; application controls references          | Document references; access patterns often require duplicated fields | Tree paths and duplicated data for different access patterns                  |
| Integrity                 | Transactions and foreign-key constraints     | Validation and transactions; no SQL-style foreign-key enforcement | Transactions and validation through backend/rules                    | Transactions and validation rules                                             |
| Historical reporting      | SQL filters, joins and aggregation           | Query and aggregation pipelines                                   | Indexed queries; report design may need extra processing             | Limited query model; historical reports need more application work            |
| Live dashboard            | Backend polling, SSE or WebSockets           | Backend updates; change streams where supported                   | SDK listeners                                                        | SDK listeners and native presence features                                    |
| Offline device collection | Build a local queue                          | Build a local queue                                               | Do not assume web/mobile SDK caching covers a Python device process  | Do not assume client synchronisation replaces durable Python device buffering |
| Operations                | Operate a server or use a managed host       | Self-host or use a managed deployment                             | Managed cloud service                                                | Managed cloud service                                                         |
| Main trade-off here       | Schema and server maintenance                | More application responsibility for relationships                 | Provider-specific modelling, query and billing behaviour             | Awkward growing history and cross-entity reporting                            |
| Decision                  | Proposed central database                    | Viable alternative                                                | Viable alternative for a Firebase-focused team                       | Possible current-state solution; not preferred for primary history            |

## 5. Other options and why they are not selected

| Technology        | Could it work?                                   | Decision and reason                                                                                                                                                                                                                                                        |
|-------------------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PostgreSQL        | Yes; a strong relational alternative             | Suitable for this same schema and reporting workload. MySQL is retained for consistency with the existing project proposal; spatial extensions are unnecessary.                                                                                                            |
| SQLite            | Yes, including small backend deployments         | Select it for the local device queue. It needs no separate database server. A shared central deployment with many concurrent writers is less attractive because writes are serialised per file; this does not mean SQLite is incapable of running a small web application. |
| InfluxDB          | Yes, for time-series telemetry                   | Reconsider for dense measurement streams and time-based analytics. It adds another modelling/operational choice without a clear benefit for the small temperature-sampling workload.                                                                                       |
| Redis             | Technically possible, with an appropriate design | Do not use it as the sole historical record here. It supports persistence, so “Redis cannot save data” is false. Persistence settings have durability trade-offs; a cache would be an optional later role.                                                                 |
| Neo4j             | Yes, but poorly matched                          | The prototype asks for state and history, not multi-hop relationship traversal. A graph model adds learning and modelling work without solving a current requirement.                                                                                                      |
| CSV or JSON files | Suitable for exports and fixtures                | Not chosen as the shared authoritative store: locking, atomic changes, integrity checks, access management and efficient searching would need substantial custom code.                                                                                                     |

## 6. Proposed decision

**Recommendation: MySQL as the central database, SQLite as the device's durable upload queue, and a Python/FastAPI
backend.**

MySQL fits structured relationships between boxes, users, access permissions and threshold profiles, as well as
time-filtered reporting. The proposed rate of one sample every 30 seconds produces **2,880 samples per box per day**.
This workload does not by itself require a specialised time-series database. PostgreSQL would also be a sound choice;
MySQL is retained for continuity with the team's existing proposal, not because alternatives cannot perform the task.

SQLite has a separate responsibility: preserve pending samples on the device when the network is unavailable. It is not
a second competing central database. Proposed intervals are starting values for testing, not medical requirements.

## 7. Proposed relational schema and queries

```sql
CREATE TABLE boxes
(
    box_id       VARCHAR(64) PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    last_seen_at DATETIME(6) NULL
) ENGINE=InnoDB;

CREATE TABLE app_users
(
    user_id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    auth_subject VARCHAR(191) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE box_access
(
    user_id BIGINT UNSIGNED NOT NULL,
    box_id  VARCHAR(64) NOT NULL,
    PRIMARY KEY (user_id, box_id),
    FOREIGN KEY (user_id) REFERENCES app_users (user_id),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id)
) ENGINE=InnoDB;

CREATE TABLE threshold_profiles
(
    profile_id  CHAR(36) PRIMARY KEY,
    box_id      VARCHAR(64)   NOT NULL,
    lower_c     DECIMAL(5, 2) NOT NULL,
    upper_c     DECIMAL(5, 2) NOT NULL,
    warning_c   DECIMAL(5, 2) NOT NULL,
    source_note TEXT          NOT NULL,
    is_demo     BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE KEY uq_profile_box (profile_id, box_id),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CHECK (lower_c < warning_c AND warning_c < upper_c),
    CHECK (is_demo IN (0, 1))
) ENGINE=InnoDB;

CREATE TABLE temperature_samples
(
    sample_id      CHAR(36) PRIMARY KEY,
    box_id         VARCHAR(64) NOT NULL,
    sequence_no    BIGINT UNSIGNED NOT NULL,
    profile_id     CHAR(36)    NOT NULL,
    observed_at    DATETIME(6) NULL,
    clock_reliable BOOLEAN     NOT NULL,
    received_at    DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    temperature_c  DECIMAL(5, 2) NULL,
    quality        ENUM('valid','sensor_error') NOT NULL,
    UNIQUE KEY uq_box_sequence (box_id, sequence_no),
    KEY            ix_box_time (box_id, observed_at),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    FOREIGN KEY (profile_id, box_id)
        REFERENCES threshold_profiles (profile_id, box_id),
    CHECK (clock_reliable IN (0, 1)),
    CHECK ((clock_reliable = 1 AND observed_at IS NOT NULL)
        OR (clock_reliable = 0 AND observed_at IS NULL)),
    CHECK ((quality = 'valid' AND temperature_c IS NOT NULL
        AND temperature_c BETWEEN -40 AND 80)
        OR (quality = 'sensor_error' AND temperature_c IS NULL))
) ENGINE=InnoDB;

-- Should Have: latest acknowledgement for a flagged sample.
CREATE TABLE sample_reviews
(
    sample_id   CHAR(36) PRIMARY KEY,
    reviewed_by BIGINT UNSIGNED NOT NULL,
    reviewed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    FOREIGN KEY (sample_id) REFERENCES temperature_samples (sample_id),
    FOREIGN KEY (reviewed_by) REFERENCES app_users (user_id)
) ENGINE=InnoDB;
```

### Latest sample for an authorised user

```sql
SELECT s.sample_id,
       s.sequence_no,
       s.temperature_c,
       s.quality,
       s.observed_at,
       s.clock_reliable,
       s.received_at,
       p.lower_c,
       p.upper_c,
       p.is_demo,
       b.last_seen_at,
       CASE
           WHEN s.quality <> 'valid' THEN 'unknown'
           WHEN s.temperature_c < p.lower_c OR s.temperature_c > p.upper_c THEN 'Alert'
           WHEN s.temperature_c >= p.warning_c THEN 'Warning'
           ELSE 'Normal' END AS recorded_band
FROM temperature_samples s
         JOIN threshold_profiles p ON p.profile_id = s.profile_id
         JOIN boxes b ON b.box_id = s.box_id
         JOIN box_access a ON a.box_id = s.box_id
WHERE a.user_id = %s AND s.box_id = %s
ORDER BY s.sequence_no DESC
    LIMIT 1;
```

### Temperature history

```sql
SELECT s.sample_id,
       s.observed_at,
       s.temperature_c,
       s.quality,
       s.sequence_no,
       p.lower_c,
       p.upper_c
FROM temperature_samples s
         JOIN threshold_profiles p ON p.profile_id = s.profile_id
         JOIN box_access a ON a.box_id = s.box_id
WHERE a.user_id = %s
  AND s.box_id = %s
  AND s.clock_reliable = 1
  AND s.observed_at >= %s
  AND s.observed_at
    < %s
ORDER BY s.observed_at, s.sequence_no;
```

### Out-of-range observations

```sql
SELECT s.sample_id,
       s.observed_at,
       s.temperature_c,
       p.lower_c,
       p.upper_c,
       r.reviewed_at
FROM temperature_samples s
         JOIN threshold_profiles p ON p.profile_id = s.profile_id
         JOIN box_access a ON a.box_id = s.box_id
         LEFT JOIN sample_reviews r ON r.sample_id = s.sample_id
WHERE a.user_id = %s
  AND s.box_id = %s
  AND s.quality = 'valid'
  AND (s.temperature_c
    < p.lower_c
   OR s.temperature_c
    > p.upper_c)
ORDER BY s.sequence_no DESC;
```

### Local SQLite queue

Persist the sample ID, box ID, sequence, profile version, observation time/clock flag, value/quality and delivery status
in one local transaction before uploading. Store the next sequence safely. Remove or mark delivered only after server
acknowledgement. A test at 30-second sampling must reconcile at least 2,880 sample attempts over 24 hours and survive a
normal restart. Report storage errors/full queues; no silent overwriting of pending data. Profile configuration is
retained locally so offline warnings still work.

## 8. Processing, security and privacy

### Processing placement

- Device loop: sample every 30 seconds, validate, classify and control local LED without internet; heartbeat every 60
  seconds when connected.
- API ingestion: authenticate device, enforce its box identity, validate and deduplicate, preserve historical times and
  profiles.
- Dashboard: show current freshness, raw history, threshold bands and flagged observations; do not rely on cron for the
  local warning.

### Security

- Per-device credentials, revocation, HTTPS, request validation and rate limiting; no central DB password on a Pi or in
  a browser.
- Application authentication plus box-level authorisation on every read, review and history endpoint; protected sessions
  and password handling or a managed identity provider.
- Restricted DB network access, protected connections, least-privilege database accounts, backups and tested restore
  procedure.
- Keep secrets out of Git; protect physical wiring, Pi storage and configuration against casual access.
- Collect no patient details, staff movement history or medication administration records. User IDs are retained only
  for access and optional review attribution.
- Ordinary database records are not a tamper-proof clinical audit trail. This is an educational prototype, not a
  certified medicine-quality assessment system.

## 9. Learning resources and references

| Ref | Resource                                                                                                                            | What to use it for                                                |
|-----|-------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| R1  | [FastAPI: SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)                                                      | Understand backend/database integration                           |
| R2  | [MySQL Connector/Python Developer Guide](https://dev.mysql.com/doc/connector-python/en/)                                            | Python connections, parameter binding and transactions            |
| R3  | [MySQL: Introduction to InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-introduction.html)                                   | Transactional storage and relational integrity                    |
| R4  | [MySQL: Optimisation and indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html)                                | Choose indexes from query patterns                                |
| R5  | [MongoDB: Schema validation](https://www.mongodb.com/docs/manual/core/schema-validation/)                                           | Validate flexible documents                                       |
| R6  | [MongoDB: Transactions](https://www.mongodb.com/docs/manual/core/transactions/)                                                     | Understand transaction capabilities and constraints               |
| R7  | [Firebase: Choose a database](https://firebase.google.com/docs/database/rtdb-vs-firestore)                                          | Distinguish Firestore from Realtime Database                      |
| R8  | [Firebase pricing](https://firebase.google.com/pricing) and [Firestore billing](https://firebase.google.com/docs/firestore/pricing) | Estimate cost using the chosen service and workload               |
| R9  | [SQLite: Appropriate uses](https://www.sqlite.org/whentouse.html)                                                                   | Understand embedded storage and concurrency trade-offs            |
| R10 | [InfluxDB 3 Core documentation](https://docs.influxdata.com/influxdb3/core/)                                                        | Evaluate a time-series-focused alternative                        |
| R11 | [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)                                     | Understand durability choices before using Redis for stored state |
| R12 | [Neo4j: Graph database concepts](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)                                 | Understand when graph modelling is useful                         |
