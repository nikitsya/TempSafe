"""Queue temperature transitions with ingestion and deliver them through Web Push."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from functools import partial

import requests
from pywebpush import WebPushException, webpush
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from tempsafe.api.push import allowed_endpoint
from tempsafe.db.session import AsyncSessionLocal
from tempsafe.monitoring.temperature import classify_temperature
from tempsafe.settings import WebPushSettings

LOGGER = logging.getLogger(__name__)


async def record_transition(db, sample, profile):
    params = dict(box=sample.box_id, seq=sample.sequence_no, observed=sample.observed_at,
                  state=classify_temperature(sample.temperature_c, sample.quality, profile),
                  sample=sample.sample_id, now=sample.received_at)
    # The ingestion transaction holds the parent box lock, including for the first observation.
    previous = (await db.execute(text("""SELECT sequence_no, observed_at, state
                                         FROM push_box_state
                                         WHERE box_id = :box FOR
                                         UPDATE"""), params)).mappings().first()
    if previous and (previous.sequence_no >= sample.sequence_no or previous.observed_at > sample.observed_at):
        return
    changed = not previous or previous.state != params["state"]
    await db.execute(text("""INSERT INTO push_box_state (box_id, sequence_no, observed_at, state, episode_id)
                             VALUES (:box, :seq, :observed, :state, :sample)
                             ON DUPLICATE KEY UPDATE sequence_no=:seq,
                                                     observed_at=:observed,
                                                     episode_id=IF(state = :state, episode_id, :sample),
                                                     state=:state"""), params)
    if changed and params["state"] in {"Warning", "Alert"}:
        await db.execute(text("""INSERT INTO push_deliveries (sample_id, endpoint_id, state, next_attempt)
                                 SELECT :sample, s.endpoint_id, :state, :now
                                 FROM push_subscriptions s
                                          JOIN box_access a ON a.user_id = s.user_id
                                 WHERE a.box_id = :box
                                   AND s.enabled = 1"""), params)


class PushSession(requests.Session):
    def request(self, *args, **kwargs):
        kwargs["allow_redirects"] = False
        return super().request(*args, **kwargs)


def send(job, ttl, settings: WebPushSettings):
    with PushSession() as http:
        response = webpush(
            subscription_info={"endpoint": job.endpoint, "keys": {"p256dh": job.p256dh, "auth": job.auth_secret}},
            data=json.dumps({"box_id": job.box_id, "state": job.state, "temperature_c": str(job.temperature_c),
                             "observed_at": job.observed_at.isoformat() + "Z", "sample_id": job.sample_id}),
            vapid_private_key=settings.private_key,
            vapid_claims={"sub": settings.subject}, ttl=ttl, timeout=5, requests_session=http,
            headers={"Urgency": "high"},
        )
        return response.status_code


async def deliver_one(db, sender, allowed_hosts: frozenset[str]):
    # Hold the job until the provider responds. Concurrent workers skip claimed jobs.
    item = await db.scalar(text("""SELECT id
                                   FROM push_deliveries
                                   WHERE status = 'pending'
                                     AND next_attempt <= UTC_TIMESTAMP(6)
                                   ORDER BY next_attempt, id
                                   LIMIT 1
                                   FOR
                                   UPDATE SKIP LOCKED"""))
    if item is None:
        return False
    job = (await db.execute(text("""SELECT d.*,
                                           t.box_id,
                                           t.observed_at,
                                           t.temperature_c,
                                           s.endpoint,
                                           s.p256dh,
                                           s.auth_secret,
                                           s.enabled,
                                           b.episode_id,
                                           a.user_id
                                    FROM push_deliveries d
                                             JOIN temperature_samples t USING (sample_id)
                                             JOIN push_subscriptions s USING (endpoint_id)
                                             JOIN push_box_state b ON b.box_id = t.box_id
                                             LEFT JOIN box_access a ON a.box_id = t.box_id AND a.user_id = s.user_id
                                    WHERE d.id = :id"""), {"id": item})).mappings().one()
    now = datetime.now(UTC).replace(tzinfo=None)
    ttl = int((job.observed_at + timedelta(seconds=90) - now).total_seconds())
    code = None
    attempts = job.attempts
    delay = 0
    if not job.enabled or job.user_id is None or job.episode_id != job.sample_id or ttl <= 0:
        status = "cancelled"
    elif not allowed_endpoint(job.endpoint, allowed_hosts):
        status = "failed"
    else:
        attempts += 1
        try:
            code = await asyncio.to_thread(sender, job, ttl)
        except WebPushException as error:
            code = error.response.status_code if error.response is not None else None
        except (requests.RequestException, OSError, ValueError):
            pass
        if code is not None and 200 <= code < 300:
            status = "accepted"
        elif code in (404, 410):
            status = "failed"
            await db.execute(text("UPDATE push_subscriptions SET enabled=0 WHERE endpoint_id=:endpoint"),
                             {"endpoint": job.endpoint_id})
        elif attempts < 4 and (code is None or code in (408, 429) or code >= 500):
            status = "pending"
            delay = 2 ** attempts
        else:
            status = "failed"
        if status != "accepted":
            LOGGER.warning("Web Push job %s attempt %s: %s (HTTP %s)", item, attempts, status, code)
    await db.execute(text("""UPDATE push_deliveries
                             SET status=:status,
                                 attempts=:attempts,
                                 http_status=:code,
                                 next_attempt=:next
                             WHERE id = :id"""),
                     dict(id=item, status=status, attempts=attempts, code=code, next=now + timedelta(seconds=delay)))
    return True


async def run_worker(settings: WebPushSettings):
    sender = partial(send, settings=settings)
    while True:
        try:
            async with AsyncSessionLocal.begin() as db:
                if await deliver_one(db, sender, settings.allowed_hosts):
                    continue
        except SQLAlchemyError:
            LOGGER.error("Web Push queue unavailable")
        await asyncio.sleep(1)
