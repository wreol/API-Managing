"""Alembic environment configuration — async SQLAlchemy 2.0 style.

Uses run_async() to bridge Alembic's synchronous migration runner with
SQLAlchemy's async engine.  The database URL is read from app.config.settings
(never from alembic.ini).
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

# Ensure the backend/ directory is on sys.path so that "app.config" and
# "app.models" resolve regardless of where the alembic command is invoked.
_backend_dir = Path(__file__).resolve().parent.parent  # backend/
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# ---------------------------------------------------------------------------
# Alembic Config object (reads alembic.ini)
# ---------------------------------------------------------------------------
config = context.config

# ---------------------------------------------------------------------------
# Logging — use the [loggers] section from alembic.ini
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target metadata — autogenerate support
# ---------------------------------------------------------------------------
from app.models import Base  # noqa: E402

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Database URL from project settings (never from alembic.ini)
# ---------------------------------------------------------------------------
from app.config import settings  # noqa: E402


def get_url() -> str:
    """Return the async database URL used for both online and offline runs."""
    return settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Offline mode — runs without a live database connection
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connects to the database via an async engine
# ---------------------------------------------------------------------------
def do_run_migrations(connection):
    """Configure and run migrations inside an async context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare server_default values (e.g. func.now())
        compare_server_default=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ---------------------------------------------------------------------------
# Dispatch — Alembic expects synchronous entry points, so wrap with asyncio
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
