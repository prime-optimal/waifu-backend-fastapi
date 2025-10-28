# Phase 1B – Alembic Migration Scaffolding

## Goal
Establish Alembic tooling and create a baseline migration that mirrors the current SQLAlchemy models so future schema changes are version-controlled and reproducible across SQLite, Neon, and Railway.

This document records required files, safe defaults, developer pre-flight, and CI/commit-check recommendations so Phase 1C+ can rely on a stable migration chain.

---
> Step 0 (recommended): create an isolated worktree for the task:
> `uv run scripts/new_task.sh 1b alembic-baseline`
> Do this before making repo changes.

---

## Context
- Phase 1A completed the Neon bootstrap, updated `.env.example`, and refreshed PR templates.
- No Alembic history exists; the application still uses `Database.create_all()` at startup.
- The ORM source-of-truth is [`src/db/models.py`](src/db/models.py:1). Alembic artifacts will be placed under the top-level [`alembic/`](alembic/env.py:1) directory in this repo.

---

## Deliverables (what we'll commit)
1. Alembic configuration and env scripts:
   - [`alembic.ini`](alembic.ini:1)
   - [`alembic/env.py`](alembic/env.py:1)
   - [`alembic/versions/0001_baseline.py`](alembic/versions/0001_baseline.py:1)
2. Baseline migration revision that matches the current ORM (no autogenerate diffs).
3. Developer documentation for local SQLite and Neon/Postgres workflows, creating migrations, and CI/commit-hook drift detection.
4. Optional helper script in `scripts/` to run migrations using the project's environment.

---

## Safe-by-default design decisions
- Alembic reads `ALEMBIC_DATABASE_URL` or `DATABASE_URL` from the environment (see [`alembic/env.py`](alembic/env.py:1)). If neither is provided, it defaults to a local ephemeral SQLite (`./dev.db`).
- `env.py` converts async DB URLs (e.g. `+asyncpg`, `+aiosqlite`) into sync equivalents for Alembic to use safely.
- Do not commit real credentials. Continue using `.env.example` as the template; developers copy to `.env` and adapt locally.

---

## Developer pre-flight (before running migration commands)
1. Ensure virtualenv & dependencies:
   - Use uv per project policy:
     - uv init (if starting fresh): `uv init --python 3.13` (only if new)
     - Install deps: `uv sync` or `uv sync --locked`
   - Activate venv (if needed): `source .venv/bin/activate`
2. Create a local `.env` from `.env.example` and set:
   - `DATABASE_URL` (or `ALEMBIC_DATABASE_URL` for one-off migrations)
   - `PYTHONPATH=.`
3. Verify DB connection:
   - `uv run python scripts/verify_db_connection.py`
   - This uses the same `DATABASE_URL` logic as the application.

---

## Local dev (SQLite) quickstart
Preferred for iteration and CI smoke checks.

1. Set up `.env` (or export in shell):
   - DATABASE_URL=sqlite+aiosqlite:///./dev.db
   - PYTHONPATH=.
2. Initialize migrations (already done in this phase): repository contains [`alembic/`](alembic/env.py:1).
3. Apply baseline:
   - uv run alembic upgrade head
   - This will use `ALEMBIC_DATABASE_URL` if present, otherwise `DATABASE_URL`, otherwise default `sqlite+aiosqlite:///./dev.db` converted for Alembic.
4. Verify:
   - uv run python scripts/verify_db_connection.py -- should succeed
   - uv run alembic history --verbose
5. Confirm `autogenerate` is idempotent:
   - uv run alembic revision --autogenerate -m "autogenerate-check"
   - If Alembic creates a new revision with operations, inspect it. For the baseline this should produce an empty/`pass` upgrade (no schema ops). If you see ops, do not commit — investigate ORM vs migration mismatch.

---

## Neon/Postgres workflow (branch DB)
When testing against Neon or other Postgres branch DBs:

1. Create a branch DB in Neon and copy credentials into your local `.env` as `ALEMBIC_DATABASE_URL` (recommended) or `DATABASE_URL`.
   - Example: ALEMBIC_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/branch_db
2. Apply migrations:
   - uv run alembic upgrade head
3. Verify using `psql` or `uv run python scripts/verify_db_connection.py`.
4. Important: Protect production. Never point `ALEMBIC_DATABASE_URL` to production unless intentionally performing a release migration. Prefer explicit environment variable and CI gating for production migrations.

---

## Creating new migrations (developer workflow)
1. Make ORM change in [`src/db/models.py`](src/db/models.py:1).
2. Run an autogenerate draft:
   - uv run alembic revision --autogenerate -m "describe change"
3. Inspect the generated migration file under `alembic/versions/`.
   - Ensure the migration correctly represents intentions and is non-destructive.
   - Add indexes / server defaults / constraints explicitly if required by your DB.
4. Apply locally:
   - uv run alembic upgrade head
5. Run the autogenerate check again to ensure no further drift:
   - uv run alembic revision --autogenerate -m "check" (no commits)
   - If this generates operations, fix either the migration or the models until autogenerate is stable.
6. Commit migration and open PR referencing `PHASE1B-<issue>`.

Notes:
- For nullable → non-nullable transitions, prefer a two-step migration (add column nullable, backfill, then alter to non-nullable).
- Prefer explicit server_default to avoid downtime/dangerous table locks on Postgres.

---

## CI / commit-hook drift detection (suggested)
Add a CI check that prevents uncommitted schema drift.

Suggested GitHub Actions job (pseudo):

- name: Alembic autogenerate drift check
  run: |
    uv sync --locked
    export PYTHONPATH=.
    export ALEMBIC_DATABASE_URL=sqlite+aiosqlite:///./ci_migration_check.db
    # Apply current migrations
    uv run alembic upgrade head
    # Create a temporary autogenerate revision to detect changes
    TMPFILE=$(mktemp /tmp/alembic_revision.XXXX.py)
    uv run alembic revision --autogenerate -m "ci-drift-check" --rev-id ci_drift_check --head-only
    # Find the most recent generated file and inspect for operations (simple heuristic)
    GEN=$(ls alembic/versions | grep ci_drift_check | head -n1 || true)
    if [ -n "$GEN" ]; then
      echo "Autogenerate produced a new migration: alembic/versions/$GEN"
      echo "This indicates schema drift between models and migrations. Please commit migrations or fix models."
      exit 1
    else
      echo "No autogenerate output — migrations are up-to-date."
    fi

Pre-commit hook (lighter): run `uv run alembic revision --autogenerate -m "precommit-check" --rev-id precommit_check` and fail if a file appears. Keep hooks fast by using SQLite ephemeral DB.

Caveat: the above heuristic uses generated filenames. Projects can improve this by running alembic's autogenerate API programmatically and asserting that there are zero operations; see `alembic.autogenerate.compare_metadata` for a stricter check.

---

## Example helper script (recommended)
Create a small wrapper at `scripts/run_migrations.sh` that:
- Ensures `PYTHONPATH=.`
- Picks `ALEMBIC_DATABASE_URL` if set, otherwise `DATABASE_URL`
- Runs `uv run alembic upgrade head`

Use:
- `./scripts/run_migrations.sh` (make executable) OR
- `uv run alembic upgrade head` (preferred, uses uv's environment)

---

## Notes for Phase 1C (multi-model tables)
- When introducing `model_results` (planned), add a migration that:
  1. Creates the table (with FK to `workflow_runs`)
  2. Adds indexes needed for query patterns (e.g. `(workflow_run_id, model_name)`)
  3. If backfilling from existing `final_asset_url`, perform in a separate, idempotent data-migration step.
- Keep data and schema migrations separate: schema migrations in Alembic; larger data backfills as standalone scripts (e.g. `scripts/backfill_model_results.py`) executed after the schema is applied.
- Ensure any multi-step transition (schema change + backfill + constraint tightening) is split into multiple revisions to maintain roll-forward safety.

---

## References in this repo
- ORM source-of-truth: [`src/db/models.py`](src/db/models.py:1)
- Alembic runtime env: [`alembic/env.py`](alembic/env.py:1)
- Baseline migration: [`alembic/versions/0001_baseline.py`](alembic/versions/0001_baseline.py:1)
- DB verification helper: [`scripts/verify_db_connection.py`](scripts/verify_db_connection.py:1)
- `.env` template: [`.env.example`](.env.example:1)

---

## Acceptance checklist (updated)
- [ ] Worktree created by `scripts/new_task.sh` and branch opened
- [ ] Alembic files committed: `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_baseline.py`
- [ ] `uv run alembic upgrade head` succeeds on fresh SQLite DB
- [ ] `uv run alembic upgrade head` succeeds on Neon branch DB (credentials in `.env`)
- [ ] `alembic history` shows baseline revision
- [ ] `alembic revision --autogenerate` against the migrated DB produces no schema ops
- [ ] Docs updated and linked from task list
- [ ] CI/commit-hook recipe added to repo (PR can add an example GitHub Actions job)
