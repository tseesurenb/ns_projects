"""
FastAPI dependencies for authentication and tenant-scoped access.
These are injected into route handlers via Depends().
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.middleware.tenant import get_current_tenant_id, set_current_tenant_id
from app.models.user import User, UserRole

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the JWT, load the user, and set tenant context.
    This is the primary auth dependency for protected routes.
    """
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing required claims.",
        )

    # Set tenant context from JWT (authoritative source)
    set_current_tenant_id(uuid.UUID(tenant_id))

    # Load user from DB
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id), User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )

    # Verify the user belongs to the claimed tenant
    if str(user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this tenant.",
        )

    return user


def require_role(*roles: UserRole):
    """
    Dependency factory that checks the current user has one of the required roles.
    Usage: Depends(require_role(UserRole.ADMIN, UserRole.OWNER))
    """

    async def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in roles]}",
            )
        return user

    return _check_role


async def get_tenant_id(
    user: User = Depends(get_current_user),
) -> uuid.UUID:
    """Convenience dependency that returns just the tenant_id."""
    return get_current_tenant_id()
