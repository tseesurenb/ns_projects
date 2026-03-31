"""
AI Agent API endpoints.
Handles chat interactions, session management, and tool configuration.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ns_base.core.dependencies import get_current_user, get_tenant_id, require_role
from ns_base.db.session import get_db
from ns_base.models.agent import AgentSession, AgentTool
from ns_base.models.user import User, UserRole
from ns_base.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentSessionResponse,
    AgentToolCreate,
    AgentToolResponse,
)
from ns_base.services.agent.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/agent", tags=["AI Agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def chat(
    payload: AgentChatRequest,
    user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI agent.
    Creates a new session if session_id is not provided.
    """
    orchestrator = AgentOrchestrator(db, tenant_id, user.id)

    try:
        result = await orchestrator.chat(
            message=payload.message,
            session_id=payload.session_id,
            model=payload.model,
            tool_names=payload.tools,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AgentChatResponse(**result)


@router.get("/sessions", response_model=list[AgentSessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all agent sessions for the current user within their tenant."""
    result = await db.execute(
        select(AgentSession)
        .where(
            AgentSession.tenant_id == tenant_id,
            AgentSession.user_id == user.id,
            AgentSession.status == "active",
        )
        .order_by(AgentSession.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) an agent session."""
    result = await db.execute(
        select(AgentSession).where(
            AgentSession.id == session_id,
            AgentSession.tenant_id == tenant_id,
            AgentSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    session.status = "archived"


# --- Tool management (admin only) ---


@router.get("/tools", response_model=list[AgentToolResponse])
async def list_tools(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all configured tools for this tenant."""
    result = await db.execute(
        select(AgentTool).where(AgentTool.tenant_id == tenant_id)
    )
    return result.scalars().all()


@router.post("/tools", response_model=AgentToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    payload: AgentToolCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.OWNER, UserRole.ADMIN)),
):
    """Create a new tool configuration for this tenant. Admin only."""
    tool = AgentTool(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        tool_type=payload.tool_type,
        configuration=payload.configuration,
    )
    db.add(tool)
    await db.flush()
    return tool
