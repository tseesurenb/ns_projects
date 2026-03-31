"""
Tenant resolution middleware.
Extracts tenant context from the request and makes it available
to all downstream handlers and services.

Supports three resolution strategies:
  1. Subdomain: acme.yourapp.com → tenant "acme"
  2. Header: X-Tenant-ID header
  3. JWT claim: tenant_id embedded in the access token
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Context variable to hold the current tenant ID throughout the request lifecycle.
# This is safe for async — each request gets its own context.
_current_tenant_id: ContextVar[Optional[uuid.UUID]] = ContextVar(
    "current_tenant_id", default=None
)


def get_current_tenant_id() -> uuid.UUID:
    """
    Retrieve the current tenant ID from request context.
    Raises an error if called outside a tenant-scoped request.
    """
    tenant_id = _current_tenant_id.get()
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context not established. Check authentication.",
        )
    return tenant_id


def set_current_tenant_id(tenant_id: uuid.UUID) -> None:
    """Set the tenant ID in the current request context."""
    _current_tenant_id.set(tenant_id)


# Paths that don't require tenant context
PUBLIC_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/health",
}


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that resolves the current tenant from the request.
    Order of resolution:
      1. X-Tenant-ID header (for API clients)
      2. Subdomain extraction (for web clients)
    JWT-based resolution happens in the auth dependency layer.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip tenant resolution for public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        tenant_id = None

        # Strategy 1: Explicit header
        header_value = request.headers.get("X-Tenant-ID")
        if header_value:
            try:
                tenant_id = uuid.UUID(header_value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Tenant-ID header format.",
                )

        # Strategy 2: Subdomain
        if tenant_id is None:
            host = request.headers.get("host", "")
            parts = host.split(".")
            if len(parts) > 2:
                # e.g., "acme.yourapp.com" → subdomain = "acme"
                # Subdomain-to-ID resolution would hit a cache/DB lookup
                # For now, we skip and rely on JWT-based resolution
                pass

        # Set context if resolved; otherwise the auth dependency will set it from JWT
        if tenant_id:
            set_current_tenant_id(tenant_id)

        response = await call_next(request)
        return response
