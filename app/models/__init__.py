"""
SQLAlchemy models for the multi-tenant SaaS platform.
Import all models here so Alembic can discover them.
"""

from app.models.tenant import Tenant, TenantPlan
from app.models.user import User, UserRole
from app.models.agent import AgentSession, AgentMessage, AgentTool
from app.models.crm import Company, Staff, ProductCategory, Product

__all__ = [
    "Tenant",
    "TenantPlan",
    "User",
    "UserRole",
    "AgentSession",
    "AgentMessage",
    "AgentTool",
    "Company",
    "Staff",
    "ProductCategory",
    "Product",
]
