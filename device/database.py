from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path(__file__).resolve().parent / "temperature_readings.db"

engine = create_engine(
    URL.create("sqlite", database=str(DB_PATH))
)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass
