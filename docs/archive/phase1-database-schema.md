# Phase 1 — Database Schema (Archived)

> **⚠️ Superseded:** This document has been split into:
> - **Phase 1A** — Neon Database Bootstrap: [`../phase1a-neon-bootstrap.md`](../phase1a-neon-bootstrap.md)
> - **Phase 1B** — Alembic Migration for Model Results: [`../phase1b-alembic-migration.md`](../phase1b-alembic-migration.md)
>
> Please use the new Phase 1A/1B documents for current work. This file is preserved for historical reference only.

 // docs/tasks/phase1-database-schema.md
 # Phase 1 — Database Schema & Repository Prep

 ## Dependency
 - **Blocking:** none (this phase must complete before Phase 2).

 ## Required .env Variables
 Ensure these are present before running tests or migrations:
 - `DATABASE_URL`
 - `NEON_DATABASE_URL` *(optional: for pointing at existing Neon instance)*
 - `PYTHONPATH=.`

 ## Tasks
 1. **ModelResult Table**
    - Add `ModelResult` SQLAlchemy model to `src/db/models.py`.
    - Fields: `id`, `workflow_run_id`, `model_name`, `status`, `asset_url`, `error_message`, `processing_time_ms`, `created_at`.
    - Set up relationships with `WorkflowRun`.

 2. **Repository Methods**
    - Extend `WorkflowRepository` with:
      - `create_model_result(...)`
      - `get_model_results(...)`
    - Ensure flush but not commit inside repository methods.

 3. **Database Bootstrap**
    - Update any `__all__`/imports for new model if needed.
    - Confirm `Database.create_all()` picks up the new table.
    - If using Neon, verify connectivity (`uv run python scripts/verify_db_connection.py`).

 ## Tests to Mock / Execute
 - `uv run pytest tests/db/test_models.py -k model_result`
 - New repository test (add under `tests/db/test_workflow_repository.py` or similar).
 - `uv run pytest tests/api/test_main_app.py::test_healthz_db`

 ## Notes
 - Use RepoPrompt MCP to show code changes before committing.
 - Task not complete without architect approval.
 - After approval: run linting (`uv run ruff check .`) and add a dev journal entry in `/docs/journal` per `JOURNAL.md`.

 ## Workflow Expectations
 1. Receive task document → review test list.
 2. Stub tests/mocks as needed.
 3. Implement feature.
 4. Run unit/integration tests + lint.
 5. Submit changes to RepoPrompt MCP for architectural review.
 6. Address feedback, rerun tests.
 7. After approval, apply real credentials/endpoints.
 8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.