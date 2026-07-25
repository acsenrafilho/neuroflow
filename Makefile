.PHONY: install test lint api frontend-build docs

install:
	poetry install
	cd frontend && npm install
	mkdir -p data/jobs data/datasets

test:
	poetry run pytest -q

lint:
	poetry run ruff check neuroflow tests
	poetry run ruff format --check neuroflow tests

api:
	poetry run neuroflow serve

frontend-build:
	cd frontend && npm run build

docs:
	poetry install --with docs
	poetry run mkdocs serve
