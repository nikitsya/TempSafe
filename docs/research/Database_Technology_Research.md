# Smart Box: Database Technology Research

## 1. What is written in which language?

| Component              | Proposed technology              | Language or format       | Role in Smart Box                                                           |
|------------------------|----------------------------------|--------------------------|-----------------------------------------------------------------------------|
| Device application     | Raspberry Pi application         | Python                   | Read the lid sensor and location receiver; timestamp and queue observations |
| Device's local storage | SQLite                           | SQL through Python       | Keep an offline upload queue on the device                                  |
| Network messages       | HTTPS API                        | JSON payloads            | Transfer observations to the backend                                        |
| Backend                | FastAPI                          | Python                   | Authenticate devices and users, validate messages and retrieve data         |
| Database connector     | MySQL Connector/Python           | Python                   | Let the backend execute parameterised MySQL queries                         |
| Central database       | MySQL with InnoDB                | SQL                      | Store boxes, access permissions and historical observations                 |
| User interface         | Web application                  | HTML, CSS and JavaScript | Display status, history and a map                                           |
| Scheduled processing   | cron running application scripts | cron syntax and Python   | Produce summaries, check stale devices and perform maintenance              |

## 2. Data requirements

| Data                  | Example fields                             | Proposed collection policy                                    | Why store it?                                       |
|-----------------------|--------------------------------------------|---------------------------------------------------------------|-----------------------------------------------------|
| Box metadata          | Box ID, display name                       | On registration or change                                     | Identify each physical box                          |
| Lid observations      | Open/closed, event ID, sequence number     | On each stable state change, plus initial state after startup | Show current state and opening history              |
| Location observations | Latitude, longitude, accuracy if available | Every 30 seconds when a valid fix is available                | Show location and movement history                  |
| Heartbeats            | Device ID, receipt timestamp               | Every 60 seconds                                              | Identify devices that have stopped reporting        |
| Observation timing    | Observed-at and received-at timestamps     | Every observation                                             | Distinguish delayed uploads from fresh observations |
| User access           | User ID and permitted box ID               | When access changes                                           | Restrict who can view each box                      |

## 3. Database categories

| Category                  | Examples                   | Data model                                         | Smart Box relevance                                                 |
|---------------------------|----------------------------|----------------------------------------------------|---------------------------------------------------------------------|
| Relational                | MySQL, PostgreSQL, SQLite  | Tables linked by keys                              | Natural fit for boxes, users, permissions and timestamped events    |
| Document                  | MongoDB, Cloud Firestore   | Collections of structured documents                | Useful when sensor payloads vary significantly                      |
| JSON tree                 | Firebase Realtime Database | Hierarchical JSON                                  | Convenient for synchronising a small current-state view             |
| Time-series               | InfluxDB                   | Timestamped measurements                           | Useful if high-volume sensor analytics becomes the main requirement |
| Key-value/data structures | Redis                      | Values and specialised structures accessed by keys | Possible cache or transient state store                             |
| Graph                     | Neo4j                      | Nodes and relationships                            | Useful for relationship traversal; not a core need here             |

## 4. Main comparison: MySQL, MongoDB and Firebase

| Criterion                 | MySQL / InnoDB                                             | MongoDB                                                           | Cloud Firestore                                                      | Firebase Realtime Database                                                    |
|---------------------------|------------------------------------------------------------|-------------------------------------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Model                     | Relational tables                                          | BSON documents                                                    | Collections and documents                                            | JSON tree                                                                     |
| Example design            | `boxes`, `observations`, `box_access`                      | Box and observation collections                                   | Box documents with observation subcollections                        | Separate box-state and history paths                                          |
| Relationships             | Foreign keys and SQL joins                                 | References or embedding; application controls references          | Document references; access patterns often require duplicated fields | Tree paths and duplicated data for different access patterns                  |
| Integrity                 | Transactions and foreign-key constraints                   | Validation and transactions; no SQL-style foreign-key enforcement | Transactions and validation through backend/rules                    | Transactions and validation rules                                             |
| Historical reporting      | SQL filters, joins and aggregation                         | Query and aggregation pipelines                                   | Indexed queries; report design may need extra processing             | Limited query model; historical reports need more application work            |
| Location                  | Store numeric coordinates; spatial features also available | GeoJSON and geospatial indexes                                    | Store coordinates; documented geohash solution for radius queries    | Coordinates can be stored; richer spatial search needs extra design           |
| Live dashboard            | Backend polling, SSE or WebSockets                         | Backend updates; change streams where supported                   | SDK listeners                                                        | SDK listeners and native presence features                                    |
| Offline device collection | Build a local queue                                        | Build a local queue                                               | Do not assume web/mobile SDK caching covers a Python device process  | Do not assume client synchronisation replaces durable Python device buffering |
| Operations                | Operate a server or use a managed host                     | Self-host or use a managed deployment                             | Managed cloud service                                                | Managed cloud service                                                         |
| Main trade-off here       | Schema and server maintenance                              | More application responsibility for relationships                 | Provider-specific modelling, query and billing behaviour             | Awkward growing history and cross-entity reporting                            |
| Decision                  | Proposed central database                                  | Viable alternative                                                | Viable alternative for a Firebase-focused team                       | Possible current-state solution; not preferred for primary history            |

## 5. Other options and why they are not selected

| Technology              | Could it work?                                   | Decision and reason                                                                                                                                                                                                                                                        |
|-------------------------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PostgreSQL with PostGIS | Yes; a strong alternative                        | Prefer it if geofencing, nearest-box searches or geographic analysis becomes central. PostGIS supplies spatial storage, indexing and queries. For a marker and simple history, it is not necessary to introduce an extension.                                              |
| SQLite                  | Yes, including small backend deployments         | Select it for the local device queue. It needs no separate database server. A shared central deployment with many concurrent writers is less attractive because writes are serialised per file; this does not mean SQLite is incapable of running a small web application. |
| InfluxDB                | Yes, for time-series telemetry                   | Reconsider for dense measurement streams and time-based analytics. It adds another modelling/operational choice without a clear benefit for the initial lid and location workload.                                                                                         |
| Redis                   | Technically possible, with an appropriate design | Do not use it as the sole historical record here. It supports persistence, so “Redis cannot save data” is false. Persistence settings have durability trade-offs; a cache would be an optional later role.                                                                 |
| Neo4j                   | Yes, but poorly matched                          | The prototype asks for state and history, not multi-hop relationship traversal. A graph model adds learning and modelling work without solving a current requirement.                                                                                                      |
| CSV or JSON files       | Suitable for exports and fixtures                | Not chosen as the shared authoritative store: locking, atomic changes, integrity checks, access management and efficient searching would need substantial custom code.                                                                                                     |

## 6. Proposed decision and integration

**Recommendation: MySQL as the central database, SQLite as the device's durable upload queue, and a Python/FastAPI
backend.**

| Boundary                  | Proposed connection                               | Responsibility                                                    |
|---------------------------|---------------------------------------------------|-------------------------------------------------------------------|
| Sensors to Raspberry Pi   | Hardware-specific GPIO or serial interface        | Device software interprets the signal                             |
| Device software to SQLite | Python's SQLite interface                         | Save pending observations locally                                 |
| Raspberry Pi to backend   | Authenticated HTTPS requests carrying JSON        | Upload observations without exposing central database credentials |
| Backend to MySQL          | MySQL Connector/Python on a restricted connection | Execute parameterised queries and transactions                    |
| Browser to backend        | Authenticated HTTPS                               | Request only boxes the user may access                            |
| Backend to dashboard      | Initially poll every 5 seconds                    | Refresh state; consider SSE/WebSockets only if needed             |

## 7. Proposed relational schema

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

CREATE TABLE observations
(
    observation_id   CHAR(36) PRIMARY KEY,
    box_id           VARCHAR(64) NOT NULL,
    sequence_no      BIGINT UNSIGNED NOT NULL,
    kind             ENUM('lid', 'location', 'heartbeat') NOT NULL,
    observed_at      DATETIME(6) NOT NULL,
    received_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    lid_state        ENUM('open', 'closed') NULL,
    is_initial_state BOOLEAN     NOT NULL DEFAULT FALSE,
    latitude         DECIMAL(9, 6) NULL,
    longitude        DECIMAL(9, 6) NULL,
    accuracy_m       DECIMAL(10, 2) NULL,
    UNIQUE KEY uq_box_sequence (box_id, sequence_no),
    KEY              ix_box_kind_sequence (box_id, kind, sequence_no),
    KEY              ix_box_kind_time (box_id, kind, observed_at),
    FOREIGN KEY (box_id) REFERENCES boxes (box_id),
    CHECK (is_initial_state IN (0, 1)),
    CHECK (kind = 'lid' OR is_initial_state = 0),
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CHECK (accuracy_m IS NULL OR accuracy_m >= 0),
    CHECK (
        (kind = 'lid' AND lid_state IS NOT NULL
            AND latitude IS NULL AND longitude IS NULL AND accuracy_m IS NULL)
            OR
        (kind = 'location' AND lid_state IS NULL
            AND latitude IS NOT NULL AND longitude IS NOT NULL)
            OR
        (kind = 'heartbeat' AND lid_state IS NULL
            AND latitude IS NULL AND longitude IS NULL AND accuracy_m IS NULL)
        )
) ENGINE=InnoDB;
```

The unique ID prevents duplicate storage, while the box/sequence constraint preserves ordering. Foreign keys prevent
observations from referring to nonexistent boxes. `box_access` implements a many-to-many user/box relationship.
Ingestion must separately authorise the sending device; a foreign key alone is not an access-control mechanism.

Set the MySQL connection/session timezone to UTC. Update `last_seen_at` from server time after a valid live device
request, including an authenticated retry; do not use an old observation timestamp as the current contact time. Latest
location queries return the last valid fix, whose age must be shown.

## 8. Security, privacy and operational limits

- Devices and browsers access the backend; central database credentials remain on the server.
- Authenticate each device separately and allow credential revocation. Check a user's box permissions for every read or
  action.
- Use HTTPS and protected database connections; keep secrets out of source control and device-upload payloads.
- Give ingestion, reporting and maintenance accounts only the database permissions they need.
- Protect device storage and backups; location history may reveal staff movements. Collect only what the prototype needs
  and restrict who can see it.
- Do not assume ordinary database rows form a tamper-proof audit trail. Stronger audit guarantees would require
  additional design.
- Store command requests separately from physical observations if remote locking is added. A successful API call is not
  evidence that a physical lock moved.

## 9. Learning resources and references

| Ref | Resource                                                                                                                            | What to use it for                                                |
|-----|-------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| R1  | [FastAPI: SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)                                                      | Understand backend/database integration                           |
| R2  | [MySQL Connector/Python Developer Guide](https://dev.mysql.com/doc/connector-python/en/)                                            | Python connections, parameter binding and transactions            |
| R3  | [MySQL: Introduction to InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-introduction.html)                                   | Transactional storage and relational integrity                    |
| R4  | [MySQL: Optimisation and indexes](https://dev.mysql.com/doc/refman/8.4/en/optimization-indexes.html)                                | Choose indexes from query patterns                                |
| R5  | [MongoDB: Geospatial queries](https://www.mongodb.com/docs/manual/geospatial-queries/)                                              | GeoJSON and location querying                                     |
| R6  | [MongoDB: Schema validation](https://www.mongodb.com/docs/manual/core/schema-validation/)                                           | Validate flexible documents                                       |
| R7  | [MongoDB: Transactions](https://www.mongodb.com/docs/manual/core/transactions/)                                                     | Understand transaction capabilities and constraints               |
| R8  | [Firebase: Choose a database](https://firebase.google.com/docs/database/rtdb-vs-firestore)                                          | Distinguish Firestore from Realtime Database                      |
| R9  | [Firestore: Geo queries](https://firebase.google.com/docs/firestore/solutions/geoqueries)                                           | Understand the documented geohash approach                        |
| R10 | [Firebase pricing](https://firebase.google.com/pricing) and [Firestore billing](https://firebase.google.com/docs/firestore/pricing) | Estimate cost using the chosen service and workload               |
| R11 | [PostGIS overview](https://postgis.net/) and [ST_DWithin](https://postgis.net/docs/ST_DWithin.html)                                 | Evaluate geographic indexing and distance queries                 |
| R12 | [SQLite: Appropriate uses](https://www.sqlite.org/whentouse.html)                                                                   | Understand embedded storage and concurrency trade-offs            |
| R13 | [InfluxDB 3 Core documentation](https://docs.influxdata.com/influxdb3/core/)                                                        | Evaluate a time-series-focused alternative                        |
| R14 | [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)                                     | Understand durability choices before using Redis for stored state |
| R15 | [Neo4j: Graph database concepts](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/)                                 | Understand when graph modelling is useful                         |
