
.PHONY: run lint fmt test migrate upgrade compose

run:
	uv run uvicorn app.main:app --reload

lint:
	uv run ruff check .

fmt:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -q

migrate:
	uv run alembic revision -m "$(m)" --autogenerate

upgrade:
	uv run alembic upgrade head

compose:
	docker compose up -d --build
