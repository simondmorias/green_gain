.PHONY: install dev build test lint clean setup

# Install all dependencies
install:
	pnpm install
	cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -e .

# Start development servers
dev:
	@echo "Starting development servers..."
	@echo "Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@make -j2 dev-web dev-api

dev-web:
	cd apps/web && pnpm dev

dev-api:
	cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload

# Build all applications
build:
	cd apps/web && pnpm build

# Run all tests
test:
	cd apps/web && pnpm test
	cd apps/api && source .venv/bin/activate && pytest

# Run linting
lint:
	cd apps/web && pnpm lint
	cd apps/api && source .venv/bin/activate && ruff check .

# Clean all build artifacts
clean:
	cd apps/web && make clean
	cd apps/api && rm -rf .venv __pycache__ .pytest_cache

# Setup development environment
setup:
	@echo "Setting up Gain development environment..."
	cd apps/web && make setup
	cd apps/api && python -m venv .venv && source .venv/bin/activate && pip install -e .
	@echo "Setup complete! Run 'make dev' to start development servers."