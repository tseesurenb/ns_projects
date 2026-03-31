"""
User model — belongs to a tenant.
Supports both platform-level and tenant-level roles.
"""

import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import BaseModel, TimestampMixin, UUIDType


class UserRole(str, enum.Enum):
    # Platform-level roles
    SUPER_ADMIN = "super_admin"
    # Tenant-level roles
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(BaseModel):
    __tablename__ = "users"

    # Identity
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Tenant association
    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    def __repr__(self) -> str:
        return f"<User {self.email} (tenant={self.tenant_id}, role={self.role.value})>"

    @property
    def is_platform_admin(self) -> bool:
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_tenant_admin(self) -> bool:
        return self.role in (UserRole.OWNER, UserRole.ADMIN)
