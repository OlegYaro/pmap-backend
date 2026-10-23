# PMAP Backend

Analytics, transaction lists, exports and admin actions of the Property Market Analytics
Platform. Backend has no database of its own: transactions live in Extraction, and Backend
reads them through the Extraction API. Redis is the TaskIQ queue for background jobs.

## Local setup

```bash
cp .env.example .env          # set EXTRACTION_API_KEY to Extraction's API_KEY
poetry install                # first run also creates poetry.lock
pre-commit install
make rebuild                  # redis, api, worker
curl localhost:8001/health
```

Extraction runs from its own repository (`make up` there) on port 8000.
Backend uses ports 8001 (API) and 6380 (Redis), so both run side by side.

## Commands

| Command | What it does |
| --- | --- |
| `make test` | runs pytest |
| `make lint` / `make check` | ruff fix and format / check only |
| `make logs` | follow container logs |
