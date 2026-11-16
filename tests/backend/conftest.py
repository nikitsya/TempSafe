"""Provide isolated database sessions and HTTP clients for backend tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from tempsafe.api.auth import accessible_boxes
from tempsafe.db.session import AsyncSessionLocal, engine, get_db
from tempsafe.main import app


@pytest.fixture
def grant_boxes(monkeypatch):
    def grant(*box_ids):
        monkeypatch.setitem(app.dependency_overrides, accessible_boxes, lambda: list(box_ids))

    return grant


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def app_lifespan():
    async with app.router.lifespan_context(app):
        yield


@pytest.fixture
async def client(app_lifespan):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as client:
        yield client


@pytest.fixture
async def db(app_lifespan, monkeypatch):
    """Let requests commit to savepoints and roll back the enclosing transaction."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            async with AsyncSessionLocal(bind=connection, join_transaction_mode="create_savepoint") as db:
                monkeypatch.setitem(app.dependency_overrides, get_db, lambda: db)
                yield db
        finally:
            await transaction.rollback()
