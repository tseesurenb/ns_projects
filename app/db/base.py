"""
SQLAlchemy declarative base with tenant-aware mixin.
All tenant-scoped models should inherit from TenantBase.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.types import TypeDecorator, CHAR
import uuid as _uuid


class UUIDType(TypeDecorator):
    """Platform-independent UUID type. Uses CHAR(32) for SQLite."""
    impl = CHAR(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, _uuid.UUID):
                return value.hex
            return _uuid.UUID(value).hex
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return _uuid.UUID(value)
        return value


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at timestamps to models."""

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TenantMixin:
    """
    Mixin that adds tenant_id to any model.
    All queries on models using this mixin MUST be scoped by tenant_id.
    The middleware and repository layers enforce this automatically.
    """

    tenant_id = Column(
        UUIDType(),
        nullable=False,
        index=True,
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base model with UUID primary key and timestamps."""

    __abstract__ = True

    id = Column(
        UUIDType(),
        primary_key=True,
        default=uuid.uuid4,
    )


class TenantBaseModel(BaseModel, TenantMixin):
    """Abstract base model for all tenant-scoped entities."""

    __abstract__ = True
