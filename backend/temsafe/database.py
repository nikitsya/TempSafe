"""Configure SQLAlchemy sessions for the TEMSAFE MySQL database."""

import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Read local settings without replacing variables already set in the environment.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Build the URL without manually escaping special characters in the password.
SQLALCHEMY_DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=os.getenv("MYSQL_USER", "temsafe"),
    password=os.environ["MYSQL_PASSWORD"],
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3307")),
    database=os.getenv("MYSQL_DATABASE", "temsafe"),
)

# Connections open on the first query; check pooled connections before reusing them.
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Follow the teaching example: create a separate session for each request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Provide the shared base for database models added in later steps."""


def get_db():
    """Supply a session to a FastAPI dependency and close it after the request."""
    with SessionLocal() as db:
        yield db
