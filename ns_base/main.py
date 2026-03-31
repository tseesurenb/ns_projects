"""
FastAPI application entry point — ns_base (multi-tenant platform base).
Manages: authentication, tenants, users, AI agent.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ns_base.api.v1.router import api_router
from ns_base.core.config import get_settings
from ns_base.middleware.tenant import TenantMiddleware

settings = get_settings()

import ns_base.models  # noqa: F401 — register all models with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    from ns_base.db.session import engine
    from ns_base.db.base import Base

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")

    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   Database tables created (SQLite)")

    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

# --- Routes ---
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# --- Static frontend ---
import os
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "project": "ns_base",
        "docs": "/docs",
        "register": "/app/register.html",
    }
