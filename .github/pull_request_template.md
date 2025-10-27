# Summary

> Link the phase task document, describe the scope of this PR, and note any deviations from the task plan.
> **Important**: Please include `Fixes #<issue>` in the summary so issues can get auto-closed.
> Include the issue directly in PR titles, descriptions, and commits using `Fixes #3`, `Closes #3`, or simply `#3`.
> Mention the RepoPrompt MCP review link or a short review summary in the PR body so the automated checks can validate architectural approval.

- Phase: <!-- e.g., [Phase 1A – Neon Bootstrap](../docs/tasks/phase1a-neon-bootstrap.md) or [Phase 1B – Alembic Migration](../docs/tasks/phase1b-alembic-migration.md) -->
- Worktree & branch: `git worktree add … && git checkout …`
- RepoPrompt MCP review summary: <!-- paste link/transcript -->


---

## Testing Checklist

> Mark the commands you ran locally. Add additional lines if needed.

- [ ] `uv run pytest …`
- [ ] `uv run ruff check .`
- [ ] `pnpm test` / `npm run test` (frontend, if applicable)
- [ ] Manual E2E: <!-- describe -->

---

## Environment & Secrets

- [ ] `.env` / secrets updated?
  - `DATABASE_URL=`
  - `NEON_DATABASE_URL=`
  - `AI_PROVIDER_URL=`
  - `AI_PROVIDER_API_KEY=`
  - `B2_*=`
  - Other:
- [ ] `.env.example` checked/updated (placeholders only — no real credentials)

---

## Documentation & Journal

- [ ] Relevant docs updated (README, data model, etc.)
- [ ] Dev journal entry created at `/docs/journal/YYYY-MM-DD-*.md` (per `docs/JOURNAL.md`)

---

## Approvals

- [ ] Architect review complete (RepoPrompt MCP)
- [ ] QA / pairing sign-off (if required)

> Final merge only after all checkboxes are satisfied and reviewer approvals recorded.
