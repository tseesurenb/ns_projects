"""
FastAPI application entry point.
Configures middleware, routers, and startup/shutdown events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.middleware.tenant import TenantMiddleware

settings = get_settings()


import app.models  # noqa: F401 — ensure all models are registered with Base.metadata


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    from app.db.session import engine
    from app.db.base import Base

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")

    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("   Database tables created (SQLite)")

    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- Middleware ---

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins in development (incl. file://)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant resolution
app.add_middleware(TenantMiddleware)

# --- Routes ---

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# --- Static frontend ---
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "register": "/app/register.html",
    }
