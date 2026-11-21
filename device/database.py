from pathlib import Path

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DB_PATH = Path(__file__).resolve().parent / "temperature_readings.db"

engine = create_async_engine(
    URL.create("sqlite+aiosqlite", database=str(DB_PATH))
)

AsyncSessionLocal = async_sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
