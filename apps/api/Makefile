# Makefile for Gain API development

.PHONY: help install dev test lint format clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Start development server"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  clean      - Clean up generated files"

# Install dependencies
install:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

# Start development server
dev:
	.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	.venv/bin/pytest tests/ -v

# Run linting
lint:
	.venv/bin/ruff check .

# Format code
format:
	.venv/bin/ruff format .

# Clean up
clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf app/routes/__pycache__
	rm -rf app/services/__pycache__
	rm -rf tests/__pycache__
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete