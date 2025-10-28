# Phase 1B – Alembic Migration Scaffolding

## Goal
Establish Alembic tooling and create a baseline migration that mirrors the current SQLAlchemy models so future schema changes are version-controlled and reproducible across SQLite, Neon, and Railway.

---

> **Step 0 – Create isolated worktree**
> `uv run scripts/new_task.sh 1b alembic-baseline`
> (Do this **before** editing any files.)

---

## Context
- Phase 1A completed Neon bootstrap and refreshed `.env.example`, docs, and PR template.
- No Alembic history exists; the app still uses `Database.create_all()` at startup.
- ORM models in `src/db/models.py` already include future tables (`processing_metrics`, `costume_popularity`, `workflow_preferences`, `model_results` placeholder).

---

## Deliverables

1. Alembic config directory (`alembic.ini`, `env.py`, `versions/`) committed to the repo.
2. Baseline revision that produces **zero diff** when running `alembic revision --autogenerate` against an empty DB that matches the current ORM.
3. Developer docs covering:
   - Local SQLite migration workflow (`uv run alembic upgrade head`)
   - Neon/Postgres workflow (branch DB, connection string in `.env`)
   - How to create new migrations (`alembic revision --autogenerate -m "message"`)
   - CI / commit-hook considerations for drift detection
4. Optional helper script or `uv` task alias for common commands.

---

## Acceptance Criteria

- [ ] Step 0 completed (worktree + branch created via `scripts/new_task.sh`)
- [ ] `uv run alembic upgrade head` succeeds on fresh SQLite DB
- [ ] Same command succeeds on Neon branch DB (credentials in `.env`)
- [ ] `alembic history` shows exactly one baseline revision
- [ ] Running `alembic revision --autogenerate` against the migrated DB produces **no changes**
- [ ] Docs updated (`docs/tasks/phase1b-alembic-migration.md` and any cross-links)
- [ ] PR opened with RepoPrompt MCP review link in body (template checkbox)

---

## Implementation Notes

- Protect production data: default Alembic env should target local DB unless `DATABASE_URL` points elsewhere.
- Keep secrets out of VCS; use `.env.example` template only.
- Preserve existing diagrams under `docs/diagrams/`; update only if table names diverge.
- Coordinate with Phase 1C planning so the migration chain is ready for multi-model tables.

---

## Next Phase
Phase 1C will sync the current dataset (local Postgres) to Railway and introduce the `model_results` table for multi-model orchestration.