
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# uv (fast package manager)
RUN pip install --no-cache-dir uv

# Project files
COPY pyproject.toml ./
RUN uv sync --frozen --no-dev

COPY . .
RUN uv sync --no-cache

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
