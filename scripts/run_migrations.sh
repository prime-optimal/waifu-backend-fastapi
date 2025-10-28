#!/usr/bin/env bash
# Helper wrapper to run Alembic migrations using the project's environment.
# - Loads local .env if present (exporting vars)
# - Prefers ALEMBIC_DATABASE_URL, then DATABASE_URL, then falls back to a local SQLite dev DB
# - Ensures PYTHONPATH is set so alembic/env.py can import src.db.models
#
# Usage:
#   chmod +x scripts/run_migrations.sh
#   ./scripts/run_migrations.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

# Load .env if present (exports variables)
if [ -f .env ]; then
  echo "Loading .env..."
  # shellcheck disable=SC1091
  set -o allexport
  # Use a subshell to avoid polluting caller when sourced in other contexts
  # We want to source plain key=value .env files; if you use more complex env management, prefer direnv or export manually.
  # shellcheck disable=SC1090
  source .env
  set +o allexport
fi

export PYTHONPATH="${PYTHONPATH:-.}"

# Determine the DB URL to use for Alembic
if [ -n "${ALEMBIC_DATABASE_URL:-}" ]; then
  DBURL="$ALEMBIC_DATABASE_URL"
elif [ -n "${DATABASE_URL:-}" ]; then
  DBURL="$DATABASE_URL"
else
  echo "No ALEMBIC_DATABASE_URL or DATABASE_URL found; defaulting to sqlite+aiosqlite:///./dev.db"
  DBURL="sqlite+aiosqlite:///./dev.db"
  export DATABASE_URL="$DBURL"
fi

echo "Using database URL for Alembic: ${DBURL}"
# Run Alembic through uv (project policy). uv will ensure the correct venv / env for tasks.
uv run alembic upgrade head