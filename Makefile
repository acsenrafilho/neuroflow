.PHONY: install test lint api frontend-build docs

install:
	poetry install
	cd frontend && npm install

test:
	poetry run pytest -q

lint:
	poetry run ruff check neuroflow tests
	poetry run ruff format --check neuroflow tests

api:
	poetry run uvicorn neuroflow.api.main:app --reload --host 127.0.0.1 --port 8000

frontend-build:
	cd frontend && npm run build

docs:
	poetry install --with docs
	poetry run mkdocs serve
