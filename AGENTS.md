<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Task Workflow Summary

1. Create or reference GitHub issue (e.g., #3, autolinked as PHASE1-3).
2. Run: `./scripts/new_task.sh PHASE1-3 database-schema`.
3. Follow the assigned phase doc in `docs/tasks/`.
4. Implement → run tests → lint.
5. Use RepoPrompt MCP to summarize and request architect approval.
6. Open PR with template (`.github/pull_request_template.md`), referencing the issue ID.
7. After approval + passing checks, merge and write journal entry in `/docs/journal/`.

## Workflow Expectations
1. Receive task document → review test list.
2. Stub tests/mocks as needed.
3. Implement feature.
4. Run unit/integration tests + lint.
5. Submit changes to RepoPrompt MCP for architectural review.
6. Address feedback, rerun tests.
7. After approval, apply real credentials/endpoints.
8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.