# Phase 1A — Neon Database Bootstrap

## Dependency
- **Blocking:** none. Complete this before Phase 2 and Phase 3 begin, so everyone works against a populated catalog.
- **Unblocks:** Phase 2 (workflow orchestration), Phase 3 (API endpoints)

## Required .env Variables
Copy these into your `.env` (the Neon DSN can point to production or a local restore):
- `NEON_DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>/<db>`
- `DATABASE_URL` (if you’re overriding the default)
- `PGPASSWORD` (optional, for CLI restore)
- `PYTHONPATH=.`

## Tasks
1. **Confirm Connectivity**
   - Update `.env` with your Neon DSN.
   - Run `uv run python scripts/verify_db_connection.py` to confirm credentials.

2. **FastAPI Uses Neon**
   - In dev `.env`, set `DATABASE_URL=$NEON_DATABASE_URL` (or update `AppSettings` to prefer `NEON_DATABASE_URL` when set).
   - Start the app (`uv run hypercorn main:app --reload`) and hit `GET /api/v1/catalog/sync` if necessary to refresh local caches.

3. **Local Fallback (optional)**
   - Provision local Postgres (`docker run --name waifu-db -p 5432:5432 -e POSTGRES_PASSWORD=… postgres:16`).
   - Restore backup: `createdb waifu_local` then `psql -d waifu_local < neon_backup_20251021_140333.sql`.
   - Swap `.env` `DATABASE_URL` to the local DSN for offline development.

4. **Document Observations**
   - Note any schema drift or missing records (log in issue/PR description).

## Tests to Mock / Execute
- `uv run pytest tests/db/test_costume_repository.py`
- `uv run pytest tests/api/test_main_app.py::test_healthz_db`
- Optional sanity: `uv run pytest tests/api/test_workflow_integration.py -k costume` to ensure prompts resolve.

## Deliverables
- RepoPrompt MCP review transcript attached.
- PR using template, referencing this doc and GitHub issue.
- Journal entry `/docs/journal/YYYY-MM-DD-phase1a-neon-bootstrap.md` after approval.

> Task is only complete once the PR is merged and the architect signs off.