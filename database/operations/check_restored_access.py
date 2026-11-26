"""Exercise the API on a disposable socket-only MySQL restoration."""

import asyncio
import secrets
import sys
from pathlib import Path

import pymysql
from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tempsafe.db.session import get_db
from tempsafe.main import app


async def check(socket):
    with pymysql.connect(unix_socket=socket, user="root", database="temsafe") as admin:
        with admin.cursor() as cursor:
            cursor.execute("SELECT @@skip_networking, @@socket")
            if cursor.fetchone() != (1, socket):
                raise RuntimeError("Expected a disposable, socket-only MySQL instance")
            cursor.execute("SELECT u.auth_subject, a.box_id FROM app_users u "
                           "JOIN box_access a USING (user_id) LIMIT 1")
            username, assigned_box = cursor.fetchone()
            password = secrets.token_urlsafe()
            cursor.execute("UPDATE app_users SET password_hash=%s WHERE auth_subject=%s",
                           (PasswordHasher().hash(password), username))
            unassigned_box = "restore-test-" + secrets.token_hex(8)
            cursor.execute("INSERT INTO boxes (box_id, name) VALUES (%s, %s)",
                           (unassigned_box, "Unassigned recovery test box"))
        admin.commit()

    engine = create_async_engine("mysql+aiomysql://tempsafe_runtime@localhost/temsafe",
                                 connect_args={"unix_socket": socket})
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def restored_database():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = restored_database
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://restore.test") as client:
            checks = [
                (await client.post("/api/login", json={"username": username, "password": password}), 204),
                (await client.get(f"/api/boxes/{assigned_box}/readings"), 200),
                (await client.get(f"/api/boxes/{unassigned_box}/readings"), 404),
                (await client.post("/api/logout"), 204),
                (await client.get(f"/api/boxes/{assigned_box}/readings"), 401),
            ]
            for response, expected in checks:
                if response.status_code != expected:
                    raise RuntimeError(
                        f"{response.request.method} returned {response.status_code}, expected {expected}")
            print("Sign-in 204, assigned box 200, unassigned box 404, sign-out 204, signed-out access 401")
    finally:
        app.dependency_overrides.pop(get_db)
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check(str(Path(sys.argv[1]).resolve())))
