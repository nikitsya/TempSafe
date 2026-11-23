"""Extra checks: repeated wrong passwords, and how long a full day of history takes to load."""
import asyncio
import time
import uuid
from datetime import UTC, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from tempsafe.db.session import engine
from tempsafe.main import app

PROFILE = "e93a4368-e11a-4f27-8b31-d55d61392548"


async def main():
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as c:
            codes = [(await c.post("/api/login", json={"username": "alice", "password": f"guess{i}"})).status_code for i
                     in range(30)]
            ok = (await c.post("/api/login", json={"username": "alice", "password": "alice-password-1"})).status_code
            print(
                f"NOTE B-35 30 wrong passwords in a row: {set(codes)}; correct password right after: {ok} (no lock-out or rate limit)")
            # One full day at 30 s
            now = datetime.now(UTC).replace(microsecond=0)
            start = now.replace(hour=0, minute=0, second=0)
            rows = []
            t = start;
            seq = 100000
            while t < now:
                rows.append({"sid": str(uuid.uuid4()), "seq": seq, "obs": t.replace(tzinfo=None),
                             "rec": t.replace(tzinfo=None)})
                seq += 1;
                t += timedelta(seconds=30)
            async with engine.begin() as conn:
                await conn.execute(text(
                    "INSERT INTO temperature_samples (sample_id, box_id, sequence_no, profile_id, observed_at, clock_reliable, received_at, temperature_c, quality) "
                    "VALUES (:sid, 'TS-01', :seq, :p, :obs, 1, :rec, 21.5, 'valid')"),
                                   [{**r, "p": PROFILE} for r in rows])
            day = now.date().isoformat()
            t0 = time.perf_counter();
            before = None;
            pages = 0;
            got = 0
            while True:
                q = f"/api/boxes/TS-01/readings?limit=100&start_date={day}&end_date={day}" + (
                    f"&before_sequence={before}" if before else "")
                page = (await c.get(q)).json();
                pages += 1;
                got += len(page)
                if len(page) < 100: break
                before = page[-1]["sequence_no"]
            print(
                f"NOTE B-36 Full day ({len(rows)} readings at 30 s): {pages} requests, {got} readings, {time.perf_counter() - t0:.2f} s on a local database")


asyncio.run(main())
