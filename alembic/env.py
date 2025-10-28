"""Alembic env.py customized for waifu-backend-fastapi.

This file:
- reads ALEMBIC_DATABASE_URL or DATABASE_URL from the environment (falling back to a local SQLite dev DB)
- converts async:// style URLs (e.g. +asyncpg / +aiosqlite) to sync counterparts so Alembic can use a synchronous engine
- sets target_metadata to the application's ORM metadata (src.db.models.Base.metadata)
- enables compare_type=True for more accurate autogenerate diffs

This env.py is intentionally defensive so running migrations targets a developer-local DB by default
and avoids accidental production writes when env vars are not explicitly configured.
"""

from __future__ import annotations

import logging
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure project root is importable so we can import src.db.models
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

try:
    # Import application models to get metadata
    from src.db.models import Base  # type: ignore
except Exception:  # pragma: no cover - defensive
    Base = None  # type: ignore

# this is the Alembic Config object, which provides access to the values within the .ini file
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")


def _select_database_url() -> str:
    """Choose a database URL from environment with safe defaults.

    Preference order:
      1. ALEMBIC_DATABASE_URL
      2. DATABASE_URL
      3. sqlite local dev DB (sqlite+aiosqlite:///./dev.db -> converted)
    """
    url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        # default local dev sqlite (matches .env.example guidance)
        url = "sqlite+aiosqlite:///./dev.db"
    return _normalize_for_alembic(url)


def _normalize_for_alembic(url: str) -> str:
    """Convert async DB URLs to sync equivalents compatible with Alembic.

    - postgresql+asyncpg -> postgresql+psycopg2
    - sqlite+aiosqlite:// -> sqlite:// (aiosqlite is asyncio-only, Alembic needs sync driver)
    """
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2")
    if "+aiosqlite" in url:
        # SQLAlchemy accepts sqlite:///./dev.db for sync usage
        return url.replace("+aiosqlite", "")
    return url


# Set sqlalchemy.url for offline mode and for engine creation
alembic_url = _select_database_url()
config.set_main_option("sqlalchemy.url", alembic_url)


# Provide the target metadata for 'autogenerate' support
target_metadata = getattr(Base, "metadata", None)

# Additional context.configure() kwargs used in run_migrations_online/offline
compare_kwargs = dict(compare_type=True, compare_server_default=True)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine, though an Engine
    would be acceptable here as well. By default, Alembic emits SQL to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **compare_kwargs,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and a connection, then configures the Alembic context with
    the connection and target metadata. We use engine_from_config so alembic.ini
    settings can be leveraged if needed.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, **compare_kwargs
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
