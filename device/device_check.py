"""Inspect an existing queue, or back it up and apply the device migration."""

import argparse
import asyncio
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from database import DB_PATH, engine, initialise_database


def connect_existing(path):
    """Open without creating a replacement for a missing production queue."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def queue_summary(connection):
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise RuntimeError("SQLite integrity check failed; preserve the file for investigation")
    columns = {row[1] for row in connection.execute("PRAGMA table_info(readings)")}
    required = {"sequence_no", "sample_id", "box_id", "profile_id", "uploaded"}
    if not required <= columns:
        raise RuntimeError("This is not the expected readings queue")
    total, latest, pending = connection.execute(
        "SELECT COUNT(*), COALESCE(MAX(sequence_no), 0), "
        "COALESCE(SUM(uploaded = 0), 0) FROM readings"
    ).fetchone()
    counter = connection.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 'readings'"
    ).fetchone()
    return (total, latest, pending, counter[0] if counter else 0)


async def upgrade_existing(path):
    """Require an existing queue and create a recoverable backup before DDL."""
    path = Path(path).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = path.with_name(f"{path.stem}-{stamp}.backup.db")
    with connect_existing(path) as source:
        before = queue_summary(source)
        # Exclusive creation avoids overwriting any earlier backup.
        with backup_path.open("xb"):
            backup_path.chmod(0o600)
        with sqlite3.connect(backup_path) as destination:
            source.backup(destination)
    print("Backup:", backup_path)
    await initialise_database()
    with connect_existing(path) as connection:
        after = queue_summary(connection)
    if before != after:
        raise RuntimeError("Queue changed during upgrade; stop all writers and inspect the backup")
    print("Migration complete; record count, maximum sequence, pending count and counter preserved")
    return backup_path


def report(path):
    print("Queue:", Path(path).resolve())
    with connect_existing(path) as connection:
        total, latest, pending, counter = queue_summary(connection)
        print(f"Readings: {total}; maximum sequence: {latest}; pending: {pending}; counter: {counter}")
        columns = {row[1] for row in connection.execute("PRAGMA table_info(readings)")}
        if "sensor_location" not in columns:
            print("Schema: legacy; stop all device processes and run --upgrade")
            return
        for location, count, waiting in connection.execute(
                "SELECT sensor_location, COUNT(*), SUM(uploaded = 0) "
                "FROM readings GROUP BY sensor_location"
        ):
            print(f"Sensor: {location}; rows: {count}; pending: {waiting}")
        for row in connection.execute(
                "SELECT sequence_no, sensor_location, sample_id, profile_id, "
                "observed_at, clock_reliable, quality, temperature_c, uploaded "
                "FROM readings ORDER BY sequence_no DESC LIMIT 6"
        ):
            print("Recent sample:", row)
        if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='device_configuration'"
        ).fetchone():
            for row in connection.execute(
                    "SELECT box_id, profile_id, lower_c, warning_c, upper_c FROM device_configuration"
            ):
                print("Saved configuration:", row)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upgrade", action="store_true",
                        help="Back up and migrate the existing queue; stop all writers first")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or newer is required")
    try:
        if args.upgrade:
            await upgrade_existing(DB_PATH)
        report(DB_PATH)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (OSError, sqlite3.Error, RuntimeError) as error:
        raise SystemExit(f"Device check failed: {error}") from error
