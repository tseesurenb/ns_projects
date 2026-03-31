"""
API v1 router — ns_base (multi-tenant platform base).
"""

from fastapi import APIRouter

from ns_base.api.v1.endpoints import auth, agent, health, users

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(agent.router)
api_router.include_router(users.router)
