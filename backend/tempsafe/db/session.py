"""Configure SQLAlchemy sessions for the TEMPSAFE MySQL database."""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Read local settings without replacing variables already set in the environment.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# Build the URL without manually escaping special characters in the password.
SQLALCHEMY_DATABASE_URL = URL.create(
    "mysql+aiomysql",
    username=os.getenv("MYSQL_USER", "tempsafe"),
    password=os.environ["MYSQL_PASSWORD"],
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3307")),
    database=os.getenv("MYSQL_DATABASE", "tempsafe"),
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Provide the shared base for database models added in later steps."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Supply a session to a FastAPI dependency and close it after the request."""
    async with AsyncSessionLocal() as db:
        yield db
