.PHONY: install test lint format build clean

install:
	pip install -e packages/django_automate
	pip install -r requirements-dev.txt

test:
	pytest packages/django_automate/tests

lint:
	ruff check packages/django_automate/src

format:
	ruff format packages/django_automate/src

typecheck:
	mypy packages/django_automate/src

clean:
	rm -rf .pytest_cache
	rm -rf build/
	rm -rf dist/
	find . -name "*.pyc" -delete
