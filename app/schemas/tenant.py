"""
Pydantic schemas for tenant operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.tenant import TenantPlan


class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantUpdate(BaseModel):
    name: str | None = None
    settings: str | None = None


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: TenantPlan
    max_users: int
    max_agent_calls_per_month: int
    agent_calls_used: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
