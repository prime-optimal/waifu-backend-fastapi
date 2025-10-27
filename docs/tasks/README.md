# Developer Task Workflow

This document explains how to pick up, implement, and close a task in the waifu-backend-fastapi repo using our standard branch/worktree + RepoPrompt MCP review process.

---

## 1. Pick Up a Task

a. Create or locate the GitHub issue (e.g., `PHASE1-3`).
b. Run the bootstrap script from the repo root:

```bash
./scripts/new_task.sh PHASE1-3 database-schema
```

c. `cd` into the new worktree:

```bash
cd ../waifu-backend-fastapi-PHASE1-3-database-schema
```

d. Copy `.env` from your main worktree or create a fresh one (see `.env.example`).
e. Open the phase-specific task doc (e.g., `docs/tasks/phase1-database-schema.md`) and review tests/requirements.

---

## 2. Implement

- Write tests first (mocked or unit) so you have a red→green loop.
- Implement the code.
- Run linting: `uv run ruff check .`
- Run tests: `uv run pytest -k <marker>`
- Commit early/often with messages that include the issue ID:
  ```
  PHASE1-3 add ModelResult table and repo methods
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

---

## 4. Open Pull Request

- Push your branch:
  ```
  git push origin PHASE1-3-database-schema
  ```

- Open a PR on GitHub. The template will prompt you for:
  - Issue link (autolinked automatically via `PHASE1-3` in title)
  - Test checklist
  - Environment/secrets confirmation
  - RepoPrompt MCP review summary
  - Documentation updates
  - Journal entry location

---

## 5. Approval & Merge

- Address feedback, re-run tests/lint.
- Ensure **all** PR-template checkboxes are ticked.
- Architect (or designated reviewer) approves.
- Merge to `main`.
- Delete branch locally and remotely:
  ```
  git worktree remove ../waifu-backend-fastapi-PHASE1-3-database-schema
  git push origin --delete PHASE1-3-database-schema
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

- Keep commits atomic; each commit message must contain the issue ID (`PHASE1-3`).
- Never force-push to `main`; always use PRs.
- If you need to switch tasks, simply `cd` back to the main worktree and spin up a new one—your in-progress worktree stays untouched.
- Worktrees are disposable—feel free to delete them once the branch is merged.

---

Need help? Ping the team or open a meta-issue with the `meta` label.
