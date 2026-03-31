"""
API v1 router — ns_crm (CRM project).
Includes base routes (auth, users) + CRM routes (products, categories).
"""

from fastapi import APIRouter

from ns_crm.api.v1.endpoints import auth, agent, health, users, products

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(agent.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
