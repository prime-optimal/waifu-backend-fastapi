# Developer Task Workflow

> **Step 0 – Create isolated worktree**
> Before you change any files run:
> `uv run scripts/new_task.sh <phase> <short-slug>`
> This spins up a clean worktree + branch so you can reset or diff at any time.

---

## Phase Catalogue & Dependency Matrix

| Phase | Goal | Status | Blocking Phase |
|-------|------|--------|----------------|
| 1A | Neon bootstrap, env template, docs refresh | ✅ DONE | — |
| 1B | Alembic baseline migration scaffolding | 🔧 READY | — |
| 1C | Railway data-sync & multi-model tables | 📋 PLANNED | 1B |
| 2  | Workflow orchestration hardening | 📋 PLANNED | 1C |
| 3  | API expansion / analytics | 📋 PLANNED | 2 |
| 4  | Frontend wiring | 📋 PLANNED | 3 |
| 5  | Docs & release polish | 📋 PLANNED | 4 |

---

## Pre-flight Checklist (apply to every phase)

- [ ] Run `uv run scripts/new_task.sh …` (see Step 0)
- [ ] Copy `.env.example` → `.env` and fill secrets (never commit real values)
- [ ] Confirm `uv run pytest` passes (unit tests)
- [ ] Run lint/format: `uv run ruff check && uv run ruff format`
- [ ] Attach RepoPrompt MCP review link in PR body (template enforces this)

---

## Commit-hook Callout

A pre-commit hook runs ruff + pytest automatically.
Install once: `uv run pre-commit install`

---

Pick your next task from the phase list above and open its detailed doc.
