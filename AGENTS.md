# Agent Guidelines for Gain Repository

## Repo Layout
- Follow the repository file/folder layout described here: ./docs/components/gain/repo_layout.md

## Build Commands
- Frontend (Next.js): `cd apps/web && pnpm install && pnpm dev`
- API (FastAPI): `cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -e . && uvicorn app.main:app --reload`
- Tests: `pytest tests/` or `pytest tests/test_specific.py::TestClass::test_method` for single test
- Lint/Format: `ruff check .` and `ruff format .` for Python, `pnpm lint` for TypeScript

## Code Style
- Python: Follow PEP 8, use type hints, Pydantic for validation
- TypeScript: Use strict mode, prefer interfaces over types, async/await over promises
- Imports: Group by stdlib, third-party, local; absolute imports for packages
- Error handling: Use structured logging, custom exceptions with error codes
- Naming: snake_case (Python), camelCase (TS), PascalCase for classes/components

## Architecture Patterns
- API Gateway (apps/api) handles all external requests via FastAPI
- Agents (services/agents) implement business logic as LangGraph workflows
- Contracts (packages/contracts) define shared schemas using Pydantic
- Workers (services/worker) process async tasks via Celery/RQ/Arq
- Use dependency injection pattern, repository pattern for data access

## Documentation
- All documents related to the repo are in ./docs/components/gain/ - the other folders in ./docs are READ ONLY
- NEVER create documentation files (*.md, *.txt, README files) in application directories (apps/, services/, packages/)
- All documentation must go in the designated docs/ folder structure
- Do not create temporary files like FIXES_APPLIED.md, CHANGES.md, or similar tracking files in code directories
