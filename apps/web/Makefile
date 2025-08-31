.PHONY: install dev build start test lint clean

# Install dependencies
install:
	pnpm install

# Start development server
dev:
	pnpm dev

# Build for production
build:
	pnpm build

# Start production server
start:
	pnpm start

# Run tests
test:
	pnpm test

# Run linting
lint:
	pnpm lint

# Clean build artifacts and node_modules
clean:
	rm -rf .next
	rm -rf node_modules
	rm -rf .pnpm-store

# Setup development environment
setup: install
	cp .env.example .env.local || true

# Run tests in watch mode
test-watch:
	pnpm test:watch