# 🚀 AgentForge — Multi AI Agent Builder

> Build, visualize, and execute multi-AI agent workflows with a modern n8n-style canvas editor.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)

## ✨ Features

- 🎨 **Visual Workflow Canvas** — Drag-and-drop node editor with SVG edge routing
- 🤖 **Multi-LLM Support** — OpenAI, Google Gemini, Groq, OpenRouter, Ollama (local)
- 💾 **Agent Memory** — Short-term buffer + long-term persistent DB-backed memory
- 🔧 **Built-in Tools** — HTTP requests, code execution, web search, custom functions
- 🏢 **Multi-Tenant** — Organization-based isolation with role-based access
- ⚡ **Async Execution** — Celery + RabbitMQ + Redis for production-grade task processing
- 🌗 **Dark / Light Mode** — Toggle between themes with smooth transitions
- 📊 **Execution Monitor** — Real-time step-by-step logs for each workflow run
- 🐳 **Docker Ready** — One-command deployment with Docker Compose

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend API** | FastAPI (async), Pydantic v2, SQLAlchemy (async) |
| **Database** | PostgreSQL (primary), SQLite (dev fallback) |
| **Task Queue** | Celery + RabbitMQ (broker) + Redis (result backend) |
| **LLM Providers** | OpenAI, Gemini, Groq, OpenRouter, Ollama |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **Frontend** | Vanilla HTML/CSS/JS (SPA, no build step) |
| **DevOps** | Docker, Docker Compose |

---

## 📁 Project Structure

```
multi-ai-agent-builder-revised/
├── app_config.yaml                # Central configuration file
├── requirements.txt               # Python dependencies
├── Dockerfile                     # App container image
├── docker-compose.yml             # Multi-service orchestration
├── entrypoint.sh                  # Docker entrypoint script
│
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration loader (YAML + env vars)
│   ├── database.py                # Async SQLAlchemy setup
│   ├── logging_config.py          # Structured logging
│   │
│   ├── api/                       # REST API endpoints
│   │   ├── auth.py                # Register, login, /me
│   │   ├── agents.py              # Agent CRUD + nodes/edges + workflow save
│   │   ├── executions.py          # Execute agents, view runs & logs
│   │   └── providers.py           # Available node types catalog
│   │
│   ├── core/
│   │   ├── security.py            # JWT + password hashing
│   │   └── dependencies.py        # FastAPI dependency injection
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── user.py                # Tenant, User
│   │   ├── agent.py               # Agent, AgentNode, AgentEdge
│   │   ├── execution.py           # Execution, ExecutionLog
│   │   └── memory.py              # MemoryStore
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── auth.py                # Auth DTOs
│   │   ├── agent.py               # Agent/Node/Edge DTOs
│   │   └── execution.py           # Execution DTOs
│   │
│   ├── engine/                    # Workflow execution engine
│   │   ├── executor.py            # DAG-based workflow executor
│   │   ├── node_registry.py       # Node/Provider factories
│   │   ├── llm_providers/         # OpenAI, Gemini, Groq, OpenRouter, Ollama
│   │   ├── memory/                # Buffer + Persistent memory
│   │   ├── tools/                 # HTTP, Code, Search tools
│   │   └── nodes/                 # Trigger, Agent, LLM, Memory, Condition, Output
│   │
│   └── workers/
│       └── celery_app.py          # Celery tasks for async execution
│
└── frontend/
    ├── index.html                 # SPA entry point
    ├── css/styles.css             # Design system (dark/light themes)
    └── js/
        ├── api.js                 # Fetch-based API client
        ├── nodes.js               # Node type definitions
        ├── canvas.js              # Visual workflow editor
        ├── dashboard.js           # Dashboard & agent management
        ├── execution.js           # Execution monitor
        └── app.js                 # Router, auth, theme toggle
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **PostgreSQL** (or SQLite for quick dev)
- **Redis** (for Celery result backend)
- **RabbitMQ** (for Celery broker)

### Option 1: Local Development Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd multi-ai-agent-builder-revised

# 2. Create virtual environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the app
# Edit app_config.yaml with your settings:
#   - Database URL (PostgreSQL or SQLite)
#   - LLM API keys (OpenAI, Gemini, Groq, etc.)
#   - Redis & RabbitMQ URLs
#   - JWT secret key (change in production!)

# 5. Start the FastAPI server
python -m backend.main
# or
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 6. (Optional) Start Celery worker for async execution
celery -A backend.workers.celery_app worker --loglevel=info

# 7. Open in browser
# http://localhost:8000
```

### Option 2: Docker Compose (Recommended)

```bash
# 1. Clone the repo
git clone <repo-url>
cd multi-ai-agent-builder-revised

# 2. Set environment variables (or edit app_config.yaml)
export OPENAI_API_KEY=your-key-here
export GEMINI_API_KEY=your-key-here

# 3. Build and start all services
docker compose up -d --build

# Services started:
#   - App (FastAPI): http://localhost:8000
#   - PostgreSQL: localhost:5432
#   - Redis: localhost:6379
#   - RabbitMQ: localhost:5672 (management: http://localhost:15672)
#   - Celery Worker: background processing

# 4. View logs
docker compose logs -f app

# 5. Stop all services
docker compose down
```

---

## ⚙️ Configuration

All configuration is managed through `app_config.yaml`:

```yaml
app:
  name: AgentForge
  version: "1.0.0"

database:
  url: "postgresql+asyncpg://postgres:postgres@localhost:5432/agentforge"

llm_providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4o-mini"
  gemini:
    api_key: "${GEMINI_API_KEY}"
    default_model: "gemini-2.0-flash"

auth:
  secret_key: "change-this-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 1440
```

Environment variables with `${VAR_NAME}` syntax are automatically resolved.

---

## 📡 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register new user + org |
| `POST` | `/api/auth/login` | Login & get JWT |
| `GET` | `/api/auth/me` | Current user info |
| `GET` | `/api/agents` | List agents |
| `POST` | `/api/agents` | Create agent |
| `GET` | `/api/agents/:id` | Get agent + nodes/edges |
| `PUT` | `/api/agents/:id` | Update agent |
| `DELETE` | `/api/agents/:id` | Delete agent |
| `POST` | `/api/agents/:id/nodes` | Add node |
| `POST` | `/api/agents/:id/edges` | Add edge |
| `PUT` | `/api/agents/:id/workflow` | Bulk save workflow |
| `POST` | `/api/agents/:id/execute` | Queue execution |
| `GET` | `/api/executions` | List executions |
| `GET` | `/api/executions/:id` | Execution details + logs |
| `GET` | `/api/providers/node-types` | Available node catalog |
| `GET` | `/api/health` | Health check |

---

## 🎨 Theme Support

The app supports **dark** and **light** modes with a toggle in:
- Login/Register page
- Sidebar footer

Theme preference is persisted in `localStorage`.

---

## 📝 License

MIT License