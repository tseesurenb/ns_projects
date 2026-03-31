"""
AI Agent Orchestrator — the core agent execution engine.

This service manages the agent loop:
  1. Receive user message
  2. Build context (system prompt + history + available tools)
  3. Call the LLM
  4. If the LLM requests tool calls, execute them
  5. Loop until the agent produces a final response or hits max iterations
  6. Track token usage per tenant

All operations are tenant-scoped.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.agent import AgentMessage, AgentSession, MessageRole
from app.models.tenant import Tenant
from app.services.agent.tools import ToolRegistry

settings = get_settings()


class AgentOrchestrator:
    """Manages AI agent conversations for a specific tenant."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id
        # Lazy import — only needed when actually calling the LLM
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        except ImportError:
            self.client = None
        self.tool_registry = ToolRegistry(db, tenant_id)

    async def chat(
        self,
        message: str,
        session_id: uuid.UUID | None = None,
        model: str | None = None,
        tool_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to the agent and get a response.
        Creates a new session if session_id is None.
        """
        # Check tenant usage limits
        await self._check_usage_limits()

        # Get or create session
        session = await self._get_or_create_session(session_id, model)

        # Save user message
        user_msg = AgentMessage(
            session_id=session.id,
            role=MessageRole.USER,
            content=message,
        )
        self.db.add(user_msg)
        await self.db.flush()

        # Build message history
        messages = await self._build_messages(session.id)

        # Get available tools for this tenant
        tools = await self.tool_registry.get_tools_schema(tool_names)

        # Agent loop
        model_name = model or session.model or settings.DEFAULT_MODEL
        total_input = 0
        total_output = 0
        iterations = 0
        final_response = ""

        while iterations < settings.AGENT_MAX_ITERATIONS:
            iterations += 1

            # Call the LLM
            api_params = {
                "model": model_name,
                "max_tokens": settings.MAX_TOKENS_PER_REQUEST,
                "messages": messages,
            }

            if session.system_prompt:
                api_params["system"] = session.system_prompt

            if tools:
                api_params["tools"] = tools

            response = await self.client.messages.create(**api_params)

            # Track tokens
            total_input += response.usage.input_tokens
            total_output += response.usage.output_tokens

            # Process response content blocks
            assistant_text = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    assistant_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            # Save assistant message
            assistant_msg = AgentMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT,
                content=assistant_text or "[tool_use]",
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            self.db.add(assistant_msg)

            # If no tool calls, we're done
            if response.stop_reason == "end_turn" or not tool_calls:
                final_response = assistant_text
                break

            # Execute tool calls and add results to messages
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_call in tool_calls:
                result = await self.tool_registry.execute_tool(
                    tool_call["name"], tool_call["input"]
                )

                # Save tool message
                tool_msg = AgentMessage(
                    session_id=session.id,
                    role=MessageRole.TOOL,
                    content=str(result),
                    tool_call_id=tool_call["id"],
                    tool_name=tool_call["name"],
                    tool_input=tool_call["input"],
                    tool_output={"result": result},
                )
                self.db.add(tool_msg)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_results})

        # Update session token counts
        session.total_input_tokens += total_input
        session.total_output_tokens += total_output

        # Update tenant usage
        await self._increment_usage(total_input + total_output)

        await self.db.flush()

        return {
            "session_id": session.id,
            "message": final_response,
            "tool_calls": tool_calls if tool_calls else None,
            "input_tokens": total_input,
            "output_tokens": total_output,
        }

    async def _get_or_create_session(
        self, session_id: uuid.UUID | None, model: str | None
    ) -> AgentSession:
        """Load existing session or create a new one."""
        if session_id:
            result = await self.db.execute(
                select(AgentSession).where(
                    AgentSession.id == session_id,
                    AgentSession.tenant_id == self.tenant_id,
                )
            )
            session = result.scalar_one_or_none()
            if not session:
                raise ValueError("Session not found or access denied.")
            return session

        session = AgentSession(
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            model=model or settings.DEFAULT_MODEL,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def _build_messages(self, session_id: uuid.UUID) -> list[dict]:
        """Build the message history for the LLM from the database."""
        result = await self.db.execute(
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at)
        )
        db_messages = result.scalars().all()

        messages = []
        for msg in db_messages:
            if msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({"role": "assistant", "content": msg.content})
            # Tool messages are handled as part of the conversation flow

        return messages

    async def _check_usage_limits(self) -> None:
        """Ensure the tenant hasn't exceeded their agent call quota."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise ValueError("Tenant not found.")

        if (
            tenant.max_agent_calls_per_month > 0
            and tenant.agent_calls_used >= tenant.max_agent_calls_per_month
        ):
            raise ValueError(
                f"Tenant has exceeded monthly agent call limit "
                f"({tenant.max_agent_calls_per_month}). "
                f"Upgrade your plan for more capacity."
            )

    async def _increment_usage(self, tokens_used: int) -> None:
        """Increment the tenant's agent call counter."""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == self.tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant:
            tenant.agent_calls_used += 1
