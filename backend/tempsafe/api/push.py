"""Manage browser push subscriptions for the signed-in account."""

import base64
import hashlib
import os
import re
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from tempsafe.api.auth import CurrentSession, Database

router = APIRouter(prefix="/push", tags=["Web Push"])


def allowed_endpoint(endpoint: str) -> bool:
    hosts = os.getenv("WEB_PUSH_HOSTS", "fcm.googleapis.com,updates.push.services.mozilla.com,web.push.apple.com")
    try:
        url = urlsplit(endpoint)
        return (url.scheme == "https" and url.netloc.lower() in hosts.lower().split(",")
                and url.hostname == url.netloc.lower() and bool(url.path.strip("/"))
                and not url.fragment and endpoint.isascii()
                and not any(c.isspace() or ord(c) < 32 or c == chr(127) for c in endpoint)
                and "\\" not in endpoint)
    except ValueError:
        return False


class BrowserKeys(BaseModel):
    p256dh: str = Field(max_length=100)
    auth: str = Field(max_length=32)

    @field_validator("p256dh", "auth")
    @classmethod
    def validate_key(cls, value, info):
        if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("Expected an unpadded base64url key")
        raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        if info.field_name == "auth":
            if len(raw) != 16:
                raise ValueError("Expected a 16-byte authentication secret")
        elif len(raw) == 65 and raw[0] == 4:
            ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
        else:
            raise ValueError("Expected an uncompressed P-256 key")
        return value


class Subscription(BaseModel):
    endpoint: str = Field(max_length=2048)
    keys: BrowserKeys


class PushPublicKeyResponse(BaseModel):
    application_server_key: str = Field(alias="applicationServerKey")


class PushSubscriptionResponse(BaseModel):
    id: str


@router.get("/public-key", response_model=PushPublicKeyResponse)
def public_key(session: CurrentSession):
    key = os.getenv("WEB_PUSH_PUBLIC_KEY")
    if not key or not os.getenv("WEB_PUSH_PRIVATE_KEY") or not os.getenv("WEB_PUSH_SUBJECT"):
        raise HTTPException(503, "Web Push is unavailable")
    return {"applicationServerKey": key}


@router.post("/subscriptions", response_model=PushSubscriptionResponse)
async def register(subscription: Subscription, session: CurrentSession, db: Database):
    public_key(session)
    if not allowed_endpoint(subscription.endpoint):
        raise HTTPException(422, "Unsupported push service")
    endpoint_id = hashlib.sha256(subscription.endpoint.encode()).hexdigest()
    params = dict(id=endpoint_id, user=session.user_id, endpoint=subscription.endpoint,
                  key=subscription.keys.p256dh, auth=subscription.keys.auth)
    await db.execute(text("""INSERT INTO push_subscriptions
        (endpoint_id,user_id,endpoint,p256dh,auth_secret) VALUES (:id,:user,:endpoint,:key,:auth)
        ON DUPLICATE KEY UPDATE endpoint_id=endpoint_id"""), params)
    owner = await db.scalar(text("SELECT user_id FROM push_subscriptions WHERE endpoint_id=:id FOR UPDATE"), params)
    if owner != session.user_id:
        raise HTTPException(409, "Subscription belongs to another account")
    await db.execute(text("""UPDATE push_subscriptions SET p256dh=:key, auth_secret=:auth,
        enabled=1 WHERE endpoint_id=:id AND user_id=:user"""), params)
    await db.commit()
    return {"id": endpoint_id}


@router.delete("/subscriptions/{endpoint_id}", status_code=204)
async def unsubscribe(endpoint_id: str, session: CurrentSession, db: Database):
    await db.execute(text("DELETE FROM push_subscriptions WHERE endpoint_id=:id AND user_id=:user"),
                     {"id": endpoint_id, "user": session.user_id})
    await db.commit()
