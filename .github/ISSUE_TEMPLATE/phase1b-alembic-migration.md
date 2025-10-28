---
name: "Phase 1B – Alembic Migration Scaffolding"
about: Establish Alembic baseline migrations mirroring the existing SQLAlchemy models.
title: "Phase 1B – Alembic Migration Scaffolding"
labels: ["phase:1B", "area:database", "priority:high"]
assignees: []
---

## Summary

- Set up Alembic within the FastAPI backend to mirror the current ORM schema (`src/db/models.py`).
- Create the baseline migration revision so future schema work (e.g., multi-model tables) builds on a clean history.
- Document the migration workflow for both local SQLite and Neon Postgres environments.

## Acceptance Criteria

- [ ] Alembic configuration files (`alembic.ini`, env script) checked in under the agreed path.
- [ ] `versions/` directory contains an initial revision that produces no diffs when compared to the current models.
- [ ] Running `uv run alembic upgrade head` succeeds against:
  - [ ] Local SQLite (`sqlite+aiosqlite:///./waifu.db` or equivalent).
  - [ ] Neon/Postgres connection defined in `.env`.
- [ ] Developer docs updated with:
  - [ ] Migration workflow instructions (create, upgrade, downgrade).
  - [ ] Troubleshooting tips for Neon/local connectivity.
  - [ ] How to detect ORM/migration drift (autogenerate guidance).
- [ ] Optional helper command or script documented for applying migrations (e.g., `scripts/new_task.sh` or `uv` alias), or rationale provided if skipped.

## Dependencies & Inputs

- Phase 1A environment setup (`.env.example`, Neon credentials guidance).
- Existing ORM definitions in `src/db/models.py`.
- `docs/tasks/phase1b-alembic-migration.md` for detailed steps and notes.

## Deliverables

- Alembic baseline migration files committed to the repo.
- Updated documentation (`docs/tasks/phase1b-alembic-migration.md`, `docs/tasks/README.md`, or supporting markdown).
- RepoPrompt MCP architectural review transcript link included in the eventual PR.

## Verification

- [ ] Local test run:
```bash
  uv run alembic upgrade head
  uv run pytest tests/db/test_db_health.py -v
  ```
- [ ] Neon smoke test:
```bash
    NEON_DATABASE_URL=... uv run alembic upgrade head
    scripts/verify_db_connection.py
```
- [ ] Confirm `alembic history` shows the baseline revision and the database matches the ORM (no pending migrations).

## Notes

- Do not check in real credentials or Neon URLs; rely on `.env` placeholders.
- Coordinate with Phase 1C planning to ensure new tables (e.g., `model_results`) are appended via subsequent revisions.
- Attach the RepoPrompt MCP review link in the PR body per the updated template.