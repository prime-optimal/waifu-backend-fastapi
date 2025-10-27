# Phase 1B — Alembic Migration for Model Results

## Dependency
- **Requires:** Phase 1A (DB connectivity established).
- Should land before Phase 2 commits that rely on the `model_results` table.

## Required .env Variables
- `DATABASE_URL` (point at Neon or the restored local Postgres used in Phase 1A)
- `ALEMBIC_DATABASE_URL` (optional, defaults to `DATABASE_URL`)
- `PYTHONPATH=.`

## Tasks
1. **Introduce Alembic Skeleton**
   - Add `alembic.ini` & `migrations/` directory if missing.
   - Configure `env.py` to read `ALEMBIC_DATABASE_URL` or fallback to `DATABASE_URL`.

2. **Add ModelResult Table**
   - Create new revision: `uv run alembic revision -m "add model_results table"`.
   - In migration script, create table with columns: `id`, `workflow_run_id` (FK), `model_name`, `status`, `asset_url`, `error_message`, `processing_time_ms`, `created_at`.
   - Include downward migration to drop the table.

3. **Wire Into Application**
   - Update `src/db/models.py` if combining with migration work (or ensure existing definitions match the migration).
   - Confirm `Database.create_all()` won’t conflict (we’ll eventually lean on Alembic).

4. **Run Migrations**
   - Apply: `uv run alembic upgrade head` against Neon/local DB.
   - Verify new table exists via `psql` or `uv run python scripts/verify_db_connection.py --check model_results`.

5. **Document Migration Process**
   - Update `README`/`docs/tasks/README` with instructions for running Alembic.

## Tests to Mock / Execute
- `uv run pytest tests/db/test_models.py -k model_results` (add/adjust coverage).
- `uv run pytest tests/db/test_workflow_repository.py -k model_result` once repository methods exist.
- `uv run pytest tests/api/test_main_app.py::test_healthz_db` (ensures DB still reachable after migration).
- Optional lint: `uv run ruff check migrations`.

## Deliverables
- RepoPrompt MCP review summary attached to PR.
- PR references `PHASE1B-<issue>` in title/description.
- Updated docs + `.env.example` if new variables introduced.
- Journal entry `/docs/journal/YYYY-MM-DD-phase1b-alembic-migration.md`.

> Task completes only after repo tests, Alembic migration, and architectural approval are in place.