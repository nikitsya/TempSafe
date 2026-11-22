"""Exploratory API tests for the TempSafe backend, run against a local MySQL copy.

Each check prints PASS / FAIL / NOTE with the evidence, so the report can quote it.
"""
import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from tempsafe.db.session import engine
from tempsafe.main import app

DEVICE_KEY = os.environ["TEMPSAFE_DEVICE_KEY"]
PROFILE = "e93a4368-e11a-4f27-8b31-d55d61392548"
results = []


def record(check_id, ok, title, evidence):
    status = "PASS" if ok is True else ("FAIL" if ok is False else "NOTE")
    results.append((check_id, status, title, evidence))
    print(f"{status:4} {check_id} {title}\n      {evidence}")


async def seed():
    pw = PasswordHasher().hash("alice-password-1")
    async with engine.begin() as c:
        await c.execute(text("INSERT IGNORE INTO boxes (box_id, name) VALUES ('TS-02', 'Other box')"))
        await c.execute(text("INSERT IGNORE INTO app_users (auth_subject, password_hash) VALUES ('alice', :h), ('bob', :h)"),
                        {"h": pw})
        await c.execute(text("INSERT IGNORE INTO box_access (user_id, box_id) "
                             "SELECT user_id, 'TS-01' FROM app_users WHERE auth_subject = 'alice'"))
        await c.execute(text("INSERT IGNORE INTO box_configuration (box_id, profile_id) VALUES ('TS-01', :p)"),
                        {"p": PROFILE})


def reading(seq, temp, minutes_ago=0.0, quality="valid", sample_id=None, profile=PROFILE, box="TS-01",
            observed=True, **extra):
    obs = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    body = {
        "sample_id": sample_id or str(uuid.uuid4()), "box_id": box, "sequence_no": seq, "profile_id": profile,
        "observed_at": obs.isoformat() if observed else None, "clock_reliable": observed,
        "temperature_c": temp, "quality": quality,
    }
    body.update(extra)
    return body


async def main():
    await seed()
    device = {"X-Device-Key": DEVICE_KEY}
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as anon, \
                AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as alice, \
                AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as bob, \
                AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as dev:

            # ---------- Authentication ----------
            r = await anon.get("/api/boxes/TS-01/readings")
            record("B-01", r.status_code == 401, "History without signing in is refused", f"GET history → {r.status_code}")
            r = await anon.get("/api/readings")
            record("B-02", r.status_code == 401, "Reading list without signing in is refused", f"GET /api/readings → {r.status_code}")
            r = await anon.post("/api/login", json={"username": "alice", "password": "wrong"})
            record("B-03", r.status_code == 401, "Wrong password is refused", f"{r.status_code} {r.json()}")
            r = await anon.post("/api/login", json={"username": "nobody", "password": "x"})
            record("B-04", r.status_code == 401 and r.json()["detail"] == "Invalid username or password",
                   "Unknown user gets the same message as a wrong password", f"{r.status_code} {r.json()}")
            r = await alice.post("/api/login", json={"username": "alice", "password": "alice-password-1"})
            cookie = r.headers.get("set-cookie", "")
            record("B-05", r.status_code == 204 and "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie,
                   "Sign-in cookie is HttpOnly, Secure and SameSite=Strict", cookie.split(";", 1)[1].strip() if cookie else r.status_code)
            await bob.post("/api/login", json={"username": "bob", "password": "alice-password-1"})
            r = await alice.get("/api/me")
            record("B-06", r.status_code == 200 and r.json()["box_ids"] == ["TS-01"], "Account shows the assigned box", r.json())

            # ---------- Access to boxes ----------
            r = await bob.get("/api/boxes/TS-01/readings")
            record("B-07", r.status_code == 404, "A user without the box cannot read its history", f"bob → {r.status_code} {r.json()}")
            r = await alice.get("/api/boxes/TS-02/readings")
            record("B-08", r.status_code == 404, "A box that is not assigned looks the same as an unknown box",
                   f"alice TS-02 → {r.status_code} {r.json()}; unknown → {(await alice.get('/api/boxes/XX/readings')).status_code}")
            r = await alice.get("/api/boxes/TS-01'%20OR%20'1'='1/readings")
            record("B-09", r.status_code == 404, "SQL text in the box ID returns nothing", f"→ {r.status_code}")
            r = await bob.put("/api/boxes/TS-01/configuration", json={"lower_c": 1, "warning_c": 2, "upper_c": 3})
            record("B-10", r.status_code == 404, "A user without the box cannot change its limits", f"bob PUT → {r.status_code}")

            # ---------- Device upload ----------
            r = await dev.post("/api/readings", json=reading(1, 20.0))
            record("B-11", r.status_code == 401, "Upload without the device key is refused", f"→ {r.status_code}")
            r = await dev.post("/api/readings", json=reading(1, 20.0), headers={"X-Device-Key": "x" * 40})
            record("B-12", r.status_code == 401, "Upload with a wrong key is refused", f"→ {r.status_code}")
            r = await dev.post("/api/readings", json=reading(1, 20.0, box="TS-02"), headers=device)
            record("B-13", r.status_code == 403, "The device cannot upload for another box", f"→ {r.status_code} {r.json()}")
            bad = [
                ("80.01°C", reading(2, 80.01)), ("-40.01°C", reading(2, -40.01)),
                ("3 decimals", reading(2, 21.123)), ("extra field", reading(2, 21.0, extra_field=1)),
                ("valid without temperature", reading(2, None)), ("sensor error with temperature", reading(2, 21.0, quality="sensor_error")),
                ("sequence as text", reading("2", 21.0)), ("negative sequence", reading(-1, 21.0)),
                ("observed_at without time zone", {**reading(2, 21.0), "observed_at": "2026-11-18T10:00:00"}),
            ]
            codes = []
            for name, body in bad:
                r = await dev.post("/api/readings", json=body, headers=device)
                codes.append(f"{name}: {r.status_code}")
            record("B-14", all(c.endswith("422") for c in codes), "Invalid uploads are rejected with 422", "; ".join(codes))

            # Future observation time (device clock wrong).
            future = reading(2, 21.0)
            future["observed_at"] = (datetime.now(UTC) + timedelta(days=2)).isoformat()
            r = await dev.post("/api/readings", json=future, headers=device)
            record("B-15", r.status_code == 422 if r.status_code != 200 else None,
                   "An observation time two days in the future", f"→ {r.status_code} (accepted)" if r.status_code == 200 else f"→ {r.status_code}")
            future_id = future["sample_id"]

            # ---------- Classification at the limits (FR-05: L=0, W=24, U=25) ----------
            cases = [(-0.01, "Alert"), (0.0, "Alert"), (0.01, "Normal"), (23.99, "Normal"), (24.0, "Warning"),
                     (25.0, "Warning"), (25.01, "Alert"), (None, "Unknown")]
            seq = 10
            got = []
            for temp, want in cases:
                body = reading(seq, temp, minutes_ago=60 - seq, quality="sensor_error" if temp is None else "valid")
                await dev.post("/api/readings", json=body, headers=device)
                seq += 1
            r = await alice.get("/api/boxes/TS-01/readings?limit=100")
            by_seq = {x["sequence_no"]: x["temperature_state"] for x in r.json()}
            for i, (temp, want) in enumerate(cases):
                got.append(f"{temp}→{by_seq.get(10 + i)}" + ("" if by_seq.get(10 + i) == want else f" (want {want})"))
            record("B-16", all("want" not in g for g in got), "Status at the exact limits follows FR-05", ", ".join(got))

            # ---------- Retries and conflicts (FR-10) ----------
            body = reading(30, 22.0)
            a = await dev.post("/api/readings", json=body, headers=device)
            b = await dev.post("/api/readings", json=body, headers=device)
            record("B-17", a.status_code == b.status_code == 200 and a.json()["received_at"] == b.json()["received_at"],
                   "An identical retry creates one reading and keeps its receipt time", f"{a.status_code}/{b.status_code}")
            changed = {**body, "temperature_c": 23.0}
            r = await dev.post("/api/readings", json=changed, headers=device)
            record("B-18", r.status_code == 409, "Same ID with a different temperature is a conflict", f"→ {r.status_code} {r.json()}")
            r = await dev.post("/api/readings", json=reading(30, 22.0), headers=device)
            record("B-19", r.status_code == 409, "A new ID with an existing sequence number is a conflict", f"→ {r.status_code} {r.json()}")

            # Delayed upload: an old reading arrives after a newer one.
            await dev.post("/api/readings", json=reading(41, 21.0, minutes_ago=1), headers=device)
            await dev.post("/api/readings", json=reading(40, 30.0, minutes_ago=2), headers=device)
            r = await alice.get("/api/boxes/TS-01/readings/latest")
            latest = r.json()
            record("B-20", latest["sequence_no"] == 41 and latest["temperature_state"] == "Normal",
                   "A delayed old Alert does not replace the latest reading",
                   f"latest = sequence {latest['sequence_no']}, {latest['temperature_c']}°C {latest['temperature_state']}")

            # ---------- Limits (configuration) ----------
            invalid = [({"lower_c": 24, "warning_c": 24, "upper_c": 25}, "lower = warning"),
                       ({"lower_c": 0, "warning_c": 26, "upper_c": 25}, "warning > upper"),
                       ({"lower_c": 0, "warning_c": 25, "upper_c": 25}, "warning = upper"),
                       ({"lower_c": 0, "warning_c": 24, "upper_c": 81}, "upper 81"),
                       ({"lower_c": 0, "warning_c": 24}, "missing upper")]
            codes = []
            for body, name in invalid:
                r = await alice.put("/api/boxes/TS-01/configuration", json=body)
                codes.append(f"{name}: {r.status_code}")
            record("B-21", all(c.endswith("422") for c in codes), "Limits in the wrong order are refused", "; ".join(codes))
            r1 = await alice.put("/api/boxes/TS-01/configuration", json={"lower_c": 2, "warning_c": 20, "upper_c": 22, "source_note": "Exploratory test"})
            r2 = await alice.put("/api/boxes/TS-01/configuration", json={"lower_c": 2, "warning_c": 20, "upper_c": 22, "source_note": "Exploratory test"})
            record("B-22", r1.status_code == 200 and r1.json()["profile_id"] == r2.json()["profile_id"],
                   "Saving the same limits twice does not create a second profile", f"{r1.json()['profile_id'][:8]} / {r2.json()['profile_id'][:8]}")
            new_profile = r1.json()["profile_id"]

            # The device keeps sending the old profile ID: which limits apply?
            await dev.post("/api/readings", json=reading(50, 21.0, minutes_ago=0.5), headers=device)
            r = await alice.get("/api/boxes/TS-01/readings/latest")
            x = r.json()
            record("B-23", None,
                   "New limits from Settings are not used while the device sends the old profile ID",
                   f"limits saved 2/20/22; reading 21.0°C stored with profile {x['profile']['profile_id'][:8]} "
                   f"(warning {x['profile']['warning_c']}, upper {x['profile']['upper_c']}) → {x['temperature_state']}; "
                   f"with the new limits it would be Warning")
            r = await dev.post("/api/readings", json=reading(51, 21.0, profile=new_profile, minutes_ago=0.3), headers=device)
            record("B-24", r.status_code == 200, "A reading sent with the new profile ID is accepted",
                   f"→ {r.status_code}, state {(await alice.get('/api/boxes/TS-01/readings/latest')).json()['temperature_state']}")

            # ---------- History filter ----------
            r = await alice.get("/api/boxes/TS-01/readings?start_date=2026-11-18&end_date=2026-11-17")
            record("B-25", r.status_code == 422, "Start date after end date is refused", f"→ {r.status_code} {r.json()}")
            r = await alice.get("/api/boxes/TS-01/readings?start_date=2026-11-18")
            record("B-26", r.status_code == 422, "Only one date is refused", f"→ {r.status_code}")
            codes = [f"limit={v}: {(await alice.get(f'/api/boxes/TS-01/readings?limit={v}')).status_code}" for v in (0, 101, -1, 'abc')]
            record("B-27", all(c.endswith("422") for c in codes), "Bad limit values are refused", "; ".join(codes))
            # Unreliable clock: does it appear in a date filter?
            await dev.post("/api/readings", json=reading(60, 21.5, observed=False), headers=device)
            today = datetime.now(UTC).date().isoformat()
            r = await alice.get(f"/api/boxes/TS-01/readings?limit=100&start_date={today}&end_date={today}")
            seqs = [x["sequence_no"] for x in r.json()]
            r_all = await alice.get("/api/boxes/TS-01/readings?limit=100")
            record("B-28", None, "A reading with an unreliable clock is missing from date-filtered history",
                   f"sequence 60 in latest list: {60 in [x['sequence_no'] for x in r_all.json()]}; in Today filter: {60 in seqs}")
            r = await alice.get(f"/api/boxes/TS-01/readings?limit=100&start_date={today}&end_date={today}")
            record("B-29", future_id not in [x["sample_id"] for x in r.json()] and
                   any(x["sample_id"] == future_id for x in (await alice.get("/api/boxes/TS-01/readings?limit=100")).json()),
                   "A reading with a future time stays out of Today but is in the plain list",
                   "future reading (+2 days) appears only without a date filter")

            # Latest reading when the newest sample is a sensor error.
            await dev.post("/api/readings", json=reading(70, None, quality="sensor_error"), headers=device)
            r = await alice.get("/api/boxes/TS-01/readings/latest")
            s = await alice.get("/api/boxes/TS-01/status")
            record("B-30", r.json()["quality"] == "sensor_error" and s.json()["contact_status"] == "reporting",
                   "A sensor error is the latest reading and the box still counts as reporting",
                   f"latest quality {r.json()['quality']}, state {r.json()['temperature_state']}; status {s.json()['contact_status']}")
            # Latest after the future reading: by sequence, so the future one (seq 2) does not win.
            record("B-31", r.json()["sequence_no"] == 70, "Latest is chosen by sequence, not by a wrong future time",
                   f"latest sequence {r.json()['sequence_no']}")

            # ---------- Sign-out ----------
            r = await alice.post("/api/logout")
            r2 = await alice.get("/api/me")
            record("B-32", r.status_code == 204 and r2.status_code == 401, "After sign-out the session no longer works",
                   f"logout {r.status_code}, then /api/me {r2.status_code}")
            r = await anon.get("/api/health")
            record("B-33", r.status_code == 200, "Health check works without signing in", f"{r.status_code} {r.json()}")
            r = await anon.get("/api/boxes/TS-01/readings", headers={"Origin": "https://evil.example"})
            record("B-34", "access-control-allow-origin" not in r.headers, "No CORS header for another website",
                   f"Access-Control-Allow-Origin: {r.headers.get('access-control-allow-origin')}")

    print("\nSUMMARY", sum(1 for x in results if x[1] == "PASS"), "pass,",
          sum(1 for x in results if x[1] == "FAIL"), "fail,", sum(1 for x in results if x[1] == "NOTE"), "note")


asyncio.run(main())
