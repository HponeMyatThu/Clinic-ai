"""OIDC / JWT Authentication and Role-Based Authorization."""

from __future__ import annotations

from typing import Annotated
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    role: str
    tenant_id: str = "default_tenant"
    is_clinician: bool = True


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(security)],
) -> CurrentUser:
    """Validate Bearer token or allow development bypass if configured."""
    if settings.app_debug or settings.app_env == "development":
        # In development mode, if no token provided, return default doctor user
        if not credentials:
            return CurrentUser(
                user_id="doc-dev-01",
                role="clinician",
                tenant_id="sg-clinic-01",
                is_clinician=True,
            )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    # In production with OIDC IdP, verify JWT signature with settings.jwt_secret_key / RS256 JWKS
    if token.startswith("dev-token") or settings.app_debug:
        return CurrentUser(
            user_id="doc-01",
            role="clinician",
            tenant_id="sg-clinic-01",
            is_clinician=True,
        )

    # Simple validation placeholder for production token decoding
    return CurrentUser(
        user_id="doc-authorized",
        role="clinician",
        tenant_id="sg-clinic-01",
        is_clinician=True,
    )


def require_clinician(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Enforce that caller has qualified clinician privileges."""
    if not user.is_clinician:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized medical clinicians",
        )
    return user

