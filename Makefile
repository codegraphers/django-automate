.PHONY: install test lint format build clean up down logs worker

install:
	pip install -e .
	pip install -r requirements-dev.txt

test:
	pytest tests

lint:
	ruff check src

format:
	ruff format src

typecheck:
	mypy src

clean:
	rm -rf .pytest_cache
	rm -rf build/
	rm -rf dist/
	find . -name "*.pyc" -delete

# Infrastructure & DX
up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

worker:
	celery -A automate worker -l info

