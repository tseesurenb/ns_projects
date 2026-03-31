"""
Models for ns_crm — CRM project (extends ns_users base).
"""

from ns_crm.models.tenant import Tenant, TenantPlan
from ns_crm.models.user import User, UserRole
from ns_crm.models.agent import AgentSession, AgentMessage, AgentTool
from ns_crm.models.crm import Company, Staff, ProductCategory, Product

__all__ = [
    "Tenant", "TenantPlan",
    "User", "UserRole",
    "AgentSession", "AgentMessage", "AgentTool",
    "Company", "Staff", "ProductCategory", "Product",
]
