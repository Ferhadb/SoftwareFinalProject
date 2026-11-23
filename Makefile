.DEFAULT_GOAL := help

.PHONY: help install run test lint format check docker-build docker-run up down logs clean

help: ## List available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project dependencies
	uv sync

run: ## Start the local development server
	uv run uvicorn app.main:app --reload

test: ## Run tests with coverage and require at least 60%
	uv run pytest --cov=app --cov-fail-under=60

lint: ## Check Python code quality
	uv run ruff check app tests

format: ## Format application and test code
	uv run ruff format app tests

check: lint ## Run lint, formatting checks, and tests
	uv run ruff format --check app tests
	$(MAKE) test

docker-build: ## Build the local Docker image
	docker build -t spendsmart:local .

docker-run: ## Run the image using settings from .env
	docker run --rm -p 8000:8000 --env-file .env spendsmart:local

up: ## Build and start the app and database with Compose
	docker compose up --build

down: ## Stop the Compose services
	docker compose down

logs: ## Follow application logs from Compose
	docker compose logs -f app

clean: ## Remove test, lint, and Python caches
	rm -rf .pytest_cache .ruff_cache .coverage
	find app tests -type d -name __pycache__ -prune -exec rm -rf {} +
