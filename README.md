# Multi-Tenant SaaS Platform

A foundational multi-tenant SaaS platform built with **FastAPI** and **Python**, designed to serve as the backbone for AI Agent-powered applications.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    API Gateway                       │
│              (FastAPI + Middleware)                   │
│    ┌──────────────┐  ┌───────────────────────┐      │
│    │ Tenant       │  │ Auth (JWT + RBAC)     │      │
│    │ Resolution   │  │                       │      │
│    └──────────────┘  └───────────────────────┘      │
├─────────────────────────────────────────────────────┤
│                   API v1 Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │
│  │  Auth    │  │  Tenant  │  │  AI Agent      │    │
│  │  Routes  │  │  Routes  │  │  Routes        │    │
│  └──────────┘  └──────────┘  └────────────────┘    │
├─────────────────────────────────────────────────────┤
│                 Service Layer                        │
│  ┌──────────────────────────────────────────────┐   │
│  │           Agent Orchestrator                  │   │
│  │  ┌─────────────┐  ┌───────────────────────┐  │   │
│  │  │ Tool        │  │ Conversation           │  │   │
│  │  │ Registry    │  │ Memory                 │  │   │
│  │  └─────────────┘  └───────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│                  Data Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │
│  │PostgreSQL│  │  Redis   │  │  Vector Store  │    │
│  │(tenants, │  │(cache,   │  │  (ChromaDB/    │    │
│  │ users,   │  │ queues,  │  │   pgvector)    │    │
│  │ sessions)│  │ limits)  │  │                │    │
│  └──────────┘  └──────────┘  └────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
multiTenantSaaS/
├── app/
│   ├── api/v1/endpoints/    # Route handlers
│   │   ├── auth.py          # Register, login, refresh
│   │   ├── agent.py         # Chat, sessions, tools
│   │   └── health.py        # Health check
│   ├── core/                # App configuration
│   │   ├── config.py        # Settings (env-based)
│   │   ├── security.py      # JWT & password hashing
│   │   └── dependencies.py  # Auth & tenant dependencies
│   ├── db/                  # Database setup
│   │   ├── base.py          # Base models & mixins
│   │   └── session.py       # Async session factory
│   ├── middleware/
│   │   └── tenant.py        # Tenant resolution middleware
│   ├── models/              # SQLAlchemy models
│   │   ├── tenant.py        # Tenant & plans
│   │   ├── user.py          # User & roles
│   │   └── agent.py         # Sessions, messages, tools
│   ├── schemas/             # Pydantic request/response
│   ├── services/agent/      # AI Agent engine
│   │   ├── orchestrator.py  # Agent loop & LLM calls
│   │   └── tools.py         # Tool registry & execution
│   └── main.py              # FastAPI app entry point
├── migrations/              # Alembic migrations
├── docker/                  # Docker & compose
├── tests/                   # Test suite
├── pyproject.toml           # Dependencies
└── .env.example             # Environment template
```

## Quick Start

```bash
# 1. Clone and set up environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and SECRET_KEY

# 2. Start with Docker
cd docker
docker compose up -d

# 3. Run migrations
alembic upgrade head

# 4. Access the API
open http://localhost:8000/docs
```

## Key Design Decisions

- **Shared-schema multi-tenancy**: All tenants share tables, isolated by `tenant_id`. Enforced at middleware + ORM level.
- **JWT with tenant claims**: Every token carries `tenant_id` + `role`, validated server-side on every request.
- **Agent orchestrator pattern**: Thin wrapper over Anthropic SDK with tenant-scoped tool injection and usage tracking.
- **Per-tenant tool configuration**: Each tenant configures their own tools (APIs, databases, functions) stored in the DB.
- **Usage-based limits**: Agent calls tracked per tenant per month, enforced before each LLM call.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register user + create tenant |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/agent/chat` | Send message to AI agent |
| GET | `/api/v1/agent/sessions` | List chat sessions |
| DELETE | `/api/v1/agent/sessions/{id}` | Archive a session |
| GET | `/api/v1/agent/tools` | List tenant tools |
| POST | `/api/v1/agent/tools` | Create a tool (admin) |
| GET | `/api/v1/health` | Health check |
