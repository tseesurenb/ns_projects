"""
Pydantic schemas for AI agent endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AgentChatRequest(BaseModel):
    """Send a message to the agent."""
    session_id: uuid.UUID | None = None  # None = create new session
    message: str
    model: str | None = None  # override default model
    tools: list[str] | None = None  # list of tool names to enable


class AgentChatResponse(BaseModel):
    """Response from the agent."""
    session_id: uuid.UUID
    message: str
    tool_calls: list[dict] | None = None
    input_tokens: int
    output_tokens: int


class AgentSessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    model: str
    status: str
    total_input_tokens: int
    total_output_tokens: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentToolCreate(BaseModel):
    name: str
    description: str | None = None
    tool_type: str
    configuration: dict = {}


class AgentToolResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    tool_type: str
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}
