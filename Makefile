.PHONY: setup install desktop-install test lint lint-fix api stop frontend-build docs

setup:
	@./scripts/setup.sh

install:
	poetry install
	cd frontend && npm install
	mkdir -p data/jobs data/datasets

desktop-install:
	@./scripts/install-desktop.sh

test:
	poetry run pytest -q

lint:
	poetry run ruff check neuroflow tests
	poetry run ruff format --check neuroflow tests

lint-fix:
	poetry run ruff check --fix neuroflow tests
	poetry run ruff format neuroflow tests

api:
	poetry run neuroflow serve

stop:
	@./scripts/neuroflow-stop.sh

frontend-build:
	cd frontend && npm run build

docs:
	poetry install --with docs
	poetry run mkdocs serve
