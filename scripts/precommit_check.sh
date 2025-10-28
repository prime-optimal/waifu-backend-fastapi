#!/usr/bin/env bash
# Lightweight pre-commit check to detect migration drift quickly using SQLite.
# Intended as an example for teams; place into .git/hooks/pre-commit to enable locally.
#
# Usage:
#   chmod +x scripts/precommit_check.sh
#   scripts/precommit_check.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

export PYTHONPATH="${PYTHONPATH:-.}"
export ALEMBIC_DATABASE_URL="sqlite+aiosqlite:///./.precommit_migration_check.db"

# Apply current migrations to ephemeral DB
uv run alembic upgrade head

# Draft an autogenerate revision; if any file is produced we consider it drift
REV_ID="precommit_check_$(date +%s)"
uv run alembic revision --autogenerate -m "precommit-check" --rev-id "$REV_ID" || true

GEN=$(ls alembic/versions 2>/dev/null | grep "$REV_ID" || true)
if [ -n "$GEN" ]; then
  echo "Autogenerate produced new migration(s):"
  ls -la alembic/versions | grep "$REV_ID" || true
  echo "This indicates schema drift between models and migrations. Please generate and commit migrations before committing."
  exit 1
fi

echo "No migration drift detected."