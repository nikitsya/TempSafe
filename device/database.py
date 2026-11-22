from pathlib import Path

from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DB_PATH = Path(__file__).resolve().parent / "temperature_readings.db"

engine = create_async_engine(
    URL.create("sqlite+aiosqlite", database=str(DB_PATH))
)

AsyncSessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


async def initialise_database():
    """Upgrade the shared queue without replacing readings or their identifiers."""
    import models  # Register both tables before creating an empty database.

    async with engine.connect() as connection:
        # Serialise startup migrations across the logger and publisher processes.
        await connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            await connection.run_sync(Base.metadata.create_all)
            columns = await connection.exec_driver_sql("PRAGMA table_info(readings)")
            if "sensor_location" not in {row[1] for row in columns}:
                await connection.execute(text(
                    "ALTER TABLE readings ADD COLUMN sensor_location TEXT "
                    "NOT NULL DEFAULT 'inside' "
                    "CHECK (sensor_location IN ('inside', 'outside'))"
                ))
            await connection.commit()
        except Exception:
            await connection.rollback()
            raise
