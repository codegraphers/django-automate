.PHONY: dev test lint format check doctor clean smoke help

# Configuration
PYTHON ?= python
DOCKER_COMPOSE ?= docker compose

help:
	@echo "Django Automate DX Makefile"
	@echo "---------------------------"
	@echo "make dev      - Start the full stack (Core + DB + Redis)"
	@echo "make test     - Run unit tests"
	@echo "make smoke    - Boot Django with full suite (smoke test)"
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

smoke:
	$(PYTHON) scripts/smoke_django_boot.py

lint:
	ruff check .
	mypy src/

format:
	ruff format .
	ruff check --fix .

doctor:
	$(PYTHON) manage.py doctor

clean:
	@echo "Cleaning cache and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage coverage.xml dist/ build/ site/ mkdocs.log test_output.txt
	@echo "Clean complete."
