"""
AI Agent models — sessions, messages, and tool configurations.
All scoped to a tenant for strict data isolation.
"""

import enum
import json

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from app.db.base import BaseModel, UUIDType


class JSONType(TypeDecorator):
    """Platform-independent JSON type. Stores as TEXT for SQLite."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class AgentSession(BaseModel):
    """A conversation session between a user and an AI agent."""

    __tablename__ = "agent_sessions"

    # Tenant & user scoping
    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUIDType(), ForeignKey("users.id"), nullable=False, index=True)

    # Session metadata
    title = Column(String(255), default="New Conversation")
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), default="claude-sonnet-4-20250514")
    status = Column(String(50), default="active")  # active | archived | deleted

    # Usage tracking
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)

    # Relationships
    tenant = relationship("Tenant", back_populates="agent_sessions")
    messages = relationship("AgentMessage", back_populates="session", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AgentSession {self.id} (tenant={self.tenant_id})>"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentMessage(BaseModel):
    """A single message within an agent session."""

    __tablename__ = "agent_messages"

    session_id = Column(UUIDType(), ForeignKey("agent_sessions.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)

    # For tool calls/results
    tool_call_id = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=True)
    tool_input = Column(JSONType, nullable=True)
    tool_output = Column(JSONType, nullable=True)

    # Token tracking per message
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)

    # Relationships
    session = relationship("AgentSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<AgentMessage {self.role.value} in session={self.session_id}>"


class AgentTool(BaseModel):
    """
    Tool configuration per tenant.
    Each tenant can have different tools enabled for their agents.
    """

    __tablename__ = "agent_tools"

    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tool_type = Column(String(50), nullable=False)  # api | database | function
    configuration = Column(JSONType, default={})  # connection details, API keys, etc.
    is_enabled = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AgentTool {self.name} (tenant={self.tenant_id})>"
