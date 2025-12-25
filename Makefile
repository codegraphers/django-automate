.PHONY: dev test lint format check doctor clean help

# Configuration
PYTHON ?= python
DOCKER_COMPOSE ?= docker compose

help:
	@echo "Django Automate DX Makefile"
	@echo "---------------------------"
	@echo "make dev      - Start the full stack (Core + DB + Redis)"
	@echo "make test     - Run unit tests"
	@echo "make lint     - Run linters (ruff, mypy)"
	@echo "make format   - Run formatters (ruff format)"
	@echo "make doctor   - Check system health"
	@echo "make clean    - Remove artifacts"

dev:
	@echo "Starting local stack..."
	$(DOCKER_COMPOSE) --profile core up -d
	@echo "Applying migrations..."
	$(PYTHON) manage.py migrate
	@echo "Stack ready. Web: http://localhost:8000"

test:
	$(PYTHON) -m pytest tests/

lint:
	ruff check .
	mypy src/

format:
	ruff format .
	ruff check --fix .

doctor:
	$(PYTHON) manage.py doctor

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
