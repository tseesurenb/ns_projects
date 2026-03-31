"""
Health check endpoint for load balancers and monitoring.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-tenant-saas"}
