---
name: Phase 1B — Alembic Migration
about: Add Alembic support and the model_results migration
title: "PHASE1B-<num>: Alembic migration for model results"
labels: ["phase1b", "backend", "database"]
assignees: ""
---

## Summary
- [ ] Review [docs/tasks/phase1b-alembic-migration.md](../../docs/tasks/phase1b-alembic-migration.md)
- [ ] Set `ALEMBIC_DATABASE_URL` / `DATABASE_URL`
- [ ] Plan RepoPrompt MCP review

## Acceptance Checklist
- [ ] Alembic revision created & applied (`uv run alembic upgrade head`)
- [ ] Tests run: `uv run pytest tests/db/test_models.py -k model_result`, `uv run pytest tests/db/test_workflow_repository.py` (new/updated cases)
- [ ] RepoPrompt MCP review logged
- [ ] PR uses template & references this issue
- [ ] Journal entry path: `/docs/journal/YYYY-MM-DD-phase1b-*.md`

## Notes
- Worktree command: `./scripts/new_task.sh PHASE1B-<num> short-slug`
- Document new env vars in `.env.example` if introduced