from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context
from app.core.config import settings
from app.db.base import Base

from app.models.user import User  # noqa: F401
from app.models.item import Item  # noqa: F401

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ---- Alembic config ----
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

TARGET_METADATA = Base.metadata

if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
    raise RuntimeError("DATABASE_URL is empty. Check your .env or settings.")


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=TARGET_METADATA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=TARGET_METADATA,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
