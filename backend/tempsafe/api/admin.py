"""Protect configuration routes until application roles are implemented."""

import secrets
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from tempsafe.settings import project_setting

bearer = HTTPBearer(auto_error=False)


def require_configuration_admin(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    """Require the server-side operator token; fail closed when unconfigured."""
    expected = project_setting("TEMPSAFE_CONFIG_ADMIN_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(503, "Configuration administration is not enabled")
    if credentials is None or not secrets.compare_digest(
            credentials.credentials.encode(), expected.encode()
    ):
        raise HTTPException(401, "Invalid administrator credentials", headers={"WWW-Authenticate": "Bearer"})
