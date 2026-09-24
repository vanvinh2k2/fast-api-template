#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-8000}"
export PATH="/venv/bin:${PATH}"
export PYTHONPATH="/app:${PYTHONPATH:-}"

echo "Running migrations..."
until alembic upgrade head; do
  echo "Migration failed, retry in 3s..."
  sleep 3
done

echo "Starting app on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
