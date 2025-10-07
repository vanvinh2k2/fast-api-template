
# FastAPI Enterprise Template (Sync SQLAlchemy, Alembic, JWT, RBAC)

A pragmatic, production-ready project layout many companies use:
- **FastAPI** + **SQLAlchemy 2.0 (sync)** + **Alembic**
- **JWT auth** (password flow) + **RBAC** scaffolding
- **Pydantic v2** settings + 12-factor `.env`
- **Dockerfile** + **docker-compose** (Postgres, API)
- Linting/format: **ruff**, **black**, **isort** + **pre-commit**
- Basic **pytest** tests

> Why sync SQLAlchemy? It's the most common deployment in many teams, simpler to operate, and integrates well with Alembic.
> If you want **async**, see the comments in `app/core/database.py` and switch the engine/session accordingly.

## Quickstart

```bash
# 1) Install with uv (recommended) or pip
uv sync

# 2) Copy env
cp .env.example .env

# 3) Start infra & app
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload

# API docs
# http://127.0.0.1:8000/docs
```

## Migrations

```bash
uv run alembic revision -m "init" --autogenerate
uv run alembic upgrade head
```

## Run tests

```bash
uv run pytest -q
```

## Structure

```
app/
  api/
    v1/
      endpoints/
      api.py
  core/           # config, logging, security, database
  db/             # session, base, init data
  models/         # SQLAlchemy models (User, Item)
  repositories/   # DB access layer
  schemas/        # Pydantic schemas
  services/       # business logic
  main.py         # FastAPI app factory
```
