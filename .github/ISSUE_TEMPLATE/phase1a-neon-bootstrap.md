---
name: Phase 1A — Neon Bootstrap
about: Point the backend at Neon / restore backup so catalog data is live
title: "PHASE1A-<num>: Neon database bootstrap"
labels: ["phase1a", "backend"]
assignees: ""
---

## Summary
- [ ] Review [docs/tasks/phase1a-neon-bootstrap.md](../../docs/tasks/phase1a-neon-bootstrap.md)
- [ ] Configure `.env` (`NEON_DATABASE_URL`, etc.)
- [ ] Plan RepoPrompt MCP review

## Acceptance Checklist
- [ ] Tests run: `uv run pytest tests/db/test_costume_repository.py`, `uv run pytest tests/api/test_main_app.py::test_healthz_db`
- [ ] RepoPrompt MCP review logged (link/summary)
- [ ] PR opened with template, references this issue ID
- [ ] Journal entry path: `/docs/journal/YYYY-MM-DD-phase1a-*.md`

## Notes
- Worktree command: `./scripts/new_task.sh PHASE1A-<num> short-slug`
- Neon backup reference: `neon_backup_20251021_140333.sql`