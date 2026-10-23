.PHONY: up down rebuild logs lint check test test-one

# Pull in .env so the settings live in one place and never reach the repo.
# Leading dash: don't fail on a fresh clone where .env doesn't exist yet.
-include .env
export

up:
	docker compose up -d

down:
	docker compose down

rebuild:
	docker compose up -d --build

logs:
	docker compose logs -f

lint:
	poetry run ruff check --fix . && poetry run ruff format .

check:
	poetry run ruff check . && poetry run ruff format --check .

test:
	poetry run pytest
