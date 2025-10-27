# Developer Task Workflow

## Phase Catalogue
| Phase    | Task Doc                                                            | Depends On         | Notes                            |
| -------- | ------------------------------------------------------------------- | ------------------ | -------------------------------- |
| Phase 1A | [Neon Database Bootstrap](phase1a-neon-bootstrap.md)                | –                  | Configure Neon/local DB          |
| Phase 1B | [Alembic Migration for Model Results](phase1b-alembic-migration.md) | Phase 1A           | Introduce Alembic, model_results |
| Phase 2  | [Workflow Orchestration](phase2-workflow-orchestration.md)          | Phase 1A, Phase 1B | Multi-model logic                |
| Phase 3  | [API Endpoints](phase3-api-endpoints.md)                            | Phase 2            | UI contracts                     |
| Phase 4  | [Frontend Integration](phase4-frontend-integration.md)              | Phase 3            | UI consumption                   |
| Phase 5  | [Docs Cleanup](phase5-cleanup-docs.md)                              | Phases 1B–3        | Final tidy-up                    |

## Dependency Matrix
- Phase 1A → Phases 2 & 3
- Phase 1B → Phase 2 (schema portions) & Phase 5
- Phase 2 → Phases 3 & 4
- Phase 3 → Phase 4
- Phase 5 may start after Phases 1A/1B but finishes after Phase 3

## Pre-flight Checklist
1. **Create or locate the GitHub issue** (e.g. `PHASE1A-1`, tracked as `#5`).
2. **Bootstrap a worktree/branch**:
   ```bash
   ./scripts/new_task.sh PHASE1A-5 neon-bootstrap
   cd ../waifu-backend-fastapi-PHASE1A-5-neon-bootstrap
   ```
3. **Set up environment variables**:
   - Copy `.env.example` → `.env`, replace placeholders with your actual credentials.
   - Never edit `.env.example` with real secrets—it remains a template only.
4. Review the phase doc for required tests before starting.

Keep the rest of the workflow (implement → RepoPrompt MCP → PR → journal record).

> **Commit hooks**
> Run `cp .githooks/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg` (or equivalent) to enforce issue IDs in commit messages. See `scripts/new_task.sh` output for reminders.

---

## 2. Implement

- Write tests first (mocked or unit) so you have a red→green loop.
- Implement the code.
- Run linting: `uv run ruff check .`
- Run tests: `uv run pytest -k <marker>`
- Commit early/often with messages that include the issue ID:
  ```
  PHASE1A-3 configure Neon DSN and verify connectivity
  ```

---

## 3. RepoPrompt MCP Review **(required)**

Before opening a PR you must request an architectural review via the RepoPrompt MCP:

- In your branch worktree, run:
  ```
  uv run python -m repoprompt review
  ```
  (or whatever command exposes the MCP endpoint)

- Paste the transcript link or summary into your PR description.
- See `.github/pull_request_template.md` for the matching checklist.

---

## 4. Open Pull Request

- Push your branch:
  ```
  git push origin PHASE1A-3-database-schema
  ```

- Open a PR on GitHub. The template will prompt you for:
  - Issue link (autolinked automatically via `PHASE1A-3` in title)
  - Test checklist
  - Environment/secrets confirmation
  - RepoPrompt MCP review summary
  - Documentation updates
  - Journal entry location
  - Include `Fixes #<issue>` (or similar) in the PR title or description. A GitHub Action enforces this.

---

## 5. Approval & Merge

- Address feedback, re-run tests/lint.
- Ensure **all** PR-template checkboxes are ticked.
- Architect (or designated reviewer) approves.
- Merge to `main`.
- Delete branch locally and remotely:
  ```
  git worktree remove ../waifu-backend-fastapi-PHASE1A-3-database-schema
  git push origin --delete PHASE1A-3-database-schema
  ```

---

## 6. Journal Entry

Immediately after merge, create a short dev journal entry:

```
docs/journal/YYYY-MM-DD-<task-slug>.md
```

Follow the format in `docs/JOURNAL.md`.

---

## Tips

- Keep commits atomic; each commit message must contain the issue ID (`PHASE1A-3`).
- Never force-push to `main`; always use PRs.
- If you need to switch tasks, simply `cd` back to the main worktree and spin up a new one—your in-progress worktree stays untouched.
- Worktrees are disposable—feel free to delete them once the branch is merged.

---

Need help? Ping the team or open a meta-issue with the `meta` label.
