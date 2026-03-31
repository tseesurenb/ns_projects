"""
Tool Registry — manages tenant-scoped tools available to the AI agent.

Each tenant can configure their own set of tools (API integrations,
database queries, custom functions). The registry loads the tenant's
enabled tools and provides them to the agent orchestrator.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ns_base.models.agent import AgentTool


class ToolRegistry:
    """
    Loads and executes tools scoped to a specific tenant.
    Tools are stored in the database with their configuration.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def get_tools_schema(
        self, tool_names: list[str] | None = None
    ) -> list[dict]:
        """
        Get the Anthropic-compatible tool schemas for the tenant's enabled tools.
        If tool_names is provided, only return those specific tools.
        """
        query = select(AgentTool).where(
            AgentTool.tenant_id == self.tenant_id,
            AgentTool.is_enabled == True,
        )

        if tool_names:
            query = query.where(AgentTool.name.in_(tool_names))

        result = await self.db.execute(query)
        db_tools = result.scalars().all()

        # Convert DB tool configs to Anthropic tool schema format
        tools = []
        for tool in db_tools:
            schema = self._build_tool_schema(tool)
            if schema:
                tools.append(schema)

        # Always include built-in tools
        tools.extend(self._get_builtin_tools())

        return tools

    def _build_tool_schema(self, tool: AgentTool) -> dict | None:
        """Convert a database tool record to Anthropic API tool schema."""
        config = tool.configuration or {}

        return {
            "name": tool.name,
            "description": tool.description or f"Tool: {tool.name}",
            "input_schema": config.get("input_schema", {
                "type": "object",
                "properties": {},
            }),
        }

    def _get_builtin_tools(self) -> list[dict]:
        """
        Built-in tools available to all tenants.
        Extend this list as you add platform-level capabilities.
        """
        return [
            {
                "name": "search_knowledge_base",
                "description": "Search the tenant's knowledge base for relevant information. Use this when you need to find specific documents, FAQs, or data.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_current_datetime",
                "description": "Get the current date and time.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    async def execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """
        Execute a tool by name with the given input.
        Routes to built-in handlers or tenant-configured external tools.
        """
        # Built-in tool handlers
        builtin_handlers = {
            "search_knowledge_base": self._handle_search_knowledge_base,
            "get_current_datetime": self._handle_get_current_datetime,
        }

        if tool_name in builtin_handlers:
            return await builtin_handlers[tool_name](tool_input)

        # Look up tenant-configured tool
        result = await self.db.execute(
            select(AgentTool).where(
                AgentTool.tenant_id == self.tenant_id,
                AgentTool.name == tool_name,
                AgentTool.is_enabled == True,
            )
        )
        tool = result.scalar_one_or_none()

        if not tool:
            return {"error": f"Tool '{tool_name}' not found or not enabled."}

        # Route to the appropriate handler based on tool_type
        if tool.tool_type == "api":
            return await self._execute_api_tool(tool, tool_input)
        elif tool.tool_type == "database":
            return await self._execute_database_tool(tool, tool_input)
        elif tool.tool_type == "function":
            return await self._execute_function_tool(tool, tool_input)

        return {"error": f"Unknown tool type: {tool.tool_type}"}

    # --- Built-in tool handlers ---

    async def _handle_search_knowledge_base(self, input_data: dict) -> dict:
        """
        Search the tenant's knowledge base.
        TODO: Integrate with vector store (ChromaDB / pgvector).
        """
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", 5)

        # Placeholder — replace with actual vector search
        return {
            "results": [],
            "message": f"Knowledge base search for '{query}' (max {max_results} results). Not yet connected to vector store.",
        }

    async def _handle_get_current_datetime(self, input_data: dict) -> dict:
        """Return the current date and time."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        return {"datetime": now.isoformat(), "timezone": "UTC"}

    # --- External tool executors ---

    async def _execute_api_tool(self, tool: AgentTool, input_data: dict) -> dict:
        """Execute an API-type tool (HTTP calls to external services)."""
        # TODO: Implement HTTP client calls using tool.configuration
        return {"message": f"API tool '{tool.name}' execution placeholder."}

    async def _execute_database_tool(self, tool: AgentTool, input_data: dict) -> dict:
        """Execute a database-type tool (SQL queries against tenant data)."""
        # TODO: Implement safe, sandboxed SQL execution
        return {"message": f"Database tool '{tool.name}' execution placeholder."}

    async def _execute_function_tool(self, tool: AgentTool, input_data: dict) -> dict:
        """Execute a function-type tool (custom Python functions)."""
        # TODO: Implement sandboxed function execution
        return {"message": f"Function tool '{tool.name}' execution placeholder."}
