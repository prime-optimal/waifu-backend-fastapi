// docs/tasks/phase5-cleanup-docs.md
# Phase 5 — Documentation & Repo Hygiene

## Dependency
- **Can run in parallel** once Phase 1 scope is understood; final pass after Phase 3 to ensure accuracy.

## Required .env Variables
No new variables; refer to Phase 2 list for reference.

## Tasks
1. **Documentation Pruning**
   - Remove/archivize redundant planning docs (`multi-model-*`, `next-steps-*`, `nano-gpt/*`, etc.).
   - Update `README.md`, `docs/data-model/README.md`, and `docs/features/multi-model-try-on.md` to reflect MVP.
   - Ensure `.env` sample includes AI provider & Neon DB hints.

2. **Diagram Refresh**
   - Regenerate ERD/service/UI diagrams with pruned entities (`ModelResult` added, analytics tables removed).
   - Update `scripts/render_mermaid_diagrams.py` output if needed.

3. **CHANGELOG & Release Notes**
   - Add entry summarizing multi-model MVP.
   - Confirm `release-checklist.md` references RepoPrompt MCP step.

4. **Repo Settings**
   - Confirm `.gitignore` covers `.artifacts/`, `.ai_output/`, `.logfire/`.

## Tests to Mock / Execute
- `uv run python scripts/render_mermaid_diagrams.py` (if applicable).
- `uv run pytest` (sanity check after doc cleanup to ensure no code regressions).
- `uv run ruff check docs/` for markdown linting (if configured).

## Notes
- Present doc diffs via RepoPrompt MCP for review.
- Final approval required before merging to main.
- Reminder: each dev logs a journal entry describing doc cleanup tasks.

## Workflow Expectations
1. Receive task document → review test list.
2. Stub tests/mocks as needed.
3. Implement feature.
4. Run unit/integration tests + lint.
5. Submit changes to RepoPrompt MCP for architectural review.
6. Address feedback, rerun tests.
7. After approval, apply real credentials/endpoints.
8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.