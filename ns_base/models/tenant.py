"""
Tenant model — the core of multi-tenancy.
Each tenant represents an organization/customer on the platform.
"""

import enum

from sqlalchemy import Boolean, Column, Enum, Integer, String, Text
from sqlalchemy.orm import relationship

from ns_base.db.base import BaseModel


class TenantPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(BaseModel):
    __tablename__ = "tenants"

    # Identity
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)  # custom domain

    # Plan & limits
    plan = Column(Enum(TenantPlan), default=TenantPlan.FREE, nullable=False)
    max_users = Column(Integer, default=5)
    max_agent_calls_per_month = Column(Integer, default=100)
    agent_calls_used = Column(Integer, default=0)

    # Settings (JSON-like config stored as text for flexibility)
    settings = Column(Text, default="{}")

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")
    agent_sessions = relationship("AgentSession", back_populates="tenant", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Tenant {self.slug} ({self.plan.value})>"
