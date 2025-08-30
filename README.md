
# Gain

Gain is a Revenue Growth Management Application target for Commercial Operators in CPG organisations.

gain/
├── apps/
│   ├── web/                      # Next.js front end (pnpm workspace)
│   └── api/                      # FastAPI gateway for all agents
│       ├── app/                  # FastAPI app package
│       │   ├── routes/           # HTTP + WebSocket/SSE endpoints
│       │   ├── services/         # thin adaptors calling agents via queue/RPC
│       │   ├── deps.py           # DI: db sessions, redis, settings
│       │   └── main.py
│       ├── tests/
│       ├── pyproject.toml
│       └── .venv/                # local venv (kept per-service)
├── services/
│   ├── agents/                   # LangGraph agents as Python packages
│   │   ├── common/               # shared graph nodes/tools (no I/O)
│   │   ├── analyst/              # e.g., Data Analyst agent (LangGraph)
│   │   ├── pricing/              # Pricing agent
│   │   ├── promos/               # Promotions agent
│   │   └── runner/               # generic runner wrappers
│   ├── worker/                   # Async workers that execute graphs
│   │   ├── worker.py             # Celery/RQ/Arq consumer entrypoint
│   │   ├── schedules.py          # APScheduler/Celery beat periodic jobs
│   │   ├── pyproject.toml
│   │   └── .venv/
│   └── jobs/                     # Declarative job specs (YAML) → schedule/queue
├── packages/
│   ├── contracts/                # API & agent contracts (single source of truth)
│   │   ├── http/                 # FastAPI/OpenAPI routers’ schemas (Pydantic)
│   │   ├── messages/             # queue message schemas (Pydantic/JSON Schema)
│   │   ├── events/               # domain events (outbox pattern)
│   │   └── python/pyproject.toml # installable lib for typing + validation
│   ├── telemetry/                # logging, tracing, metrics helpers
│   ├── persistence/              # DB models, migrations, repositories
│   │   ├── alembic/              # migrations live WITH the code
│   │   ├── models.py
│   │   ├── repo/
│   │   └── pyproject.toml
│   └── js-utils/                 # shared ts utilities for Next.js (optional)
├── scripts/                      # bootstrap, db reset, seed data
├── docs/
│   ├── ADRs/                     # architecture decision records
│   ├── API.md                    # usage + auth + SSE/WebSocket
│   ├── AGENTS.md                 # patterns, contracts, review rubric
│   └── RUNBOOKS.md               # ops guides
├── .tool-versions or uv.lock     # pin Python, Node
├── package.json                  # workspaces config (web + any TS packages)
├── pnpm-workspace.yaml
├── Makefile                      # common dev commands
├── .env.example
└── README.md

