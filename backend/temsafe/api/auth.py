"""Authenticate browser sessions and the prototype's HTTP device publisher."""

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response
from pydantic import BaseModel, SecretStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from temsafe.db.models import AppUser, BoxAccess, UserSession
from temsafe.db.session import get_db

router = APIRouter(tags=["Authentication"])
COOKIE = "__Host-tempsafe_session"
SESSION_SECONDS = 8 * 60 * 60
hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_urlsafe())
Database = Annotated[Session, Depends(get_db)]
SessionCookie = Annotated[str | None, Cookie(alias=COOKIE)]


class Login(BaseModel):
    username: str
    password: SecretStr


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def utc_now() -> datetime:
    """MySQL DATETIME values use naive UTC throughout the schema."""
    return datetime.now(UTC).replace(tzinfo=None)


@router.post("/login", status_code=204)
def login(credentials: Login, response: Response, db: Database, token: SessionCookie = None):
    password = credentials.password.get_secret_value()
    if len(credentials.username) > 191 or len(password) > 1024:
        raise HTTPException(401, "Invalid username or password")
    user = db.scalar(select(AppUser).where(AppUser.auth_subject == credentials.username))
    try:
        hasher.verify(user.password_hash if user else dummy_hash, password)
    except (InvalidHashError, VerificationError):
        raise HTTPException(401, "Invalid username or password") from None
    if user is None:
        raise HTTPException(401, "Invalid username or password")

    now = utc_now()
    db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == token_digest(token)))
    new_token = secrets.token_urlsafe(32)
    db.add(UserSession(token_hash=token_digest(new_token), user_id=user.user_id,
                       expires_at=now + timedelta(seconds=SESSION_SECONDS)))
    db.commit()
    response.set_cookie(COOKIE, new_token, max_age=SESSION_SECONDS,
                        httponly=True, secure=True, samesite="strict")
    response.headers["Cache-Control"] = "no-store"


@router.post("/logout", status_code=204)
def logout(response: Response, db: Database, token: SessionCookie = None):
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == token_digest(token)))
        db.commit()
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="strict")
    response.headers["Cache-Control"] = "no-store"


def accessible_boxes(db: Database, response: Response, token: SessionCookie = None) -> list[str]:
    session = db.get(UserSession, token_digest(token)) if token else None
    if session is None or session.expires_at <= utc_now():
        raise HTTPException(401, "Sign in to access readings")
    response.headers["Cache-Control"] = "no-store"
    return list(db.scalars(select(BoxAccess.box_id).where(BoxAccess.user_id == session.user_id)))


AllowedBoxes = Annotated[list[str], Depends(accessible_boxes)]


def require_box(box_id: str, allowed: AllowedBoxes):
    if box_id not in allowed:
        raise HTTPException(404, "Box not found")


def require_device(key: Annotated[str | None, Header(alias="X-Device-Key")] = None) -> str:
    expected = os.getenv("TEMSAFE_DEVICE_KEY", "")
    box_id = os.getenv("TEMSAFE_DEVICE_BOX_ID", "")
    if len(expected) < 32 or not box_id or not key or not secrets.compare_digest(key.encode(), expected.encode()):
        raise HTTPException(401, "Invalid device credentials")
    return box_id
