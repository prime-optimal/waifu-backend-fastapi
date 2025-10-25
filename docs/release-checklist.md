# Release & Deployment Checklist

**Last updated:** 2025-10-24

Use this checklist before merging to `main` or deploying to Railway. It covers local verification, platform-specific settings, and safe Git workflows (especially when a push is rejected because the remote branch moved).

---

## 1. Local Verification

1. **Sync dependencies**
   ```bash
   uv sync
   ```
2. **Run tests**
   ```bash
   uv run pytest
   uv run pytest tests/clients/test_ai_provider.py -v
   # Optional: live NanoGPT tests (require credentials)
   AI_PROVIDER_API_KEY=... AI_PROVIDER_URL=... uv run pytest -m external -vv
   ```
3. **Lint / format**
   ```bash
   uv run ruff check
   ```
4. **Repo hygiene**
   - Ensure `.artifacts/`, `.ai_output/`, `.logfire/`, and debug dumps under `AI_DEBUG_DIR` are ignored or cleaned.
   - Confirm generated images (from external tests) are not staged.
5. **Docs & changelog**
   - Update documentation **after** verifying the behavior it describes.
   - Refresh "Last verified" stamps where relevant.

---

## 2. Railway Deployment Checks

1. **railpack.json**
   - Confirm Hypercorn binds to the expected port:
     ```json
     "startCommand": "uv run hypercorn main:app --bind 0.0.0.0:8080"
     ```
   - Ensure the `PORT` environment variable still matches (`8080`).
2. **Railway service settings**
   - Incoming HTTP port is `8080`.
   - Environment variables (B2, AI provider, DB URL, etc.) align with documented values.
3. **Smoke test after deploy**
   ```bash
   curl -I https://<railway-domain>/healthz
   ```
   Expect `200 OK`. If you see a timeout, double-check the Hypercorn/Railway port alignment.

---

## 3. Safe Git Workflow

### When Ready to Commit
1. `git status` — verify only the intended files are staged.
2. Write descriptive commit messages that mention tests run.

### If `git push` Is Rejected
1. **Pause** — do **not** immediately `git stash` and `git pull`.
2. Inspect your state:
   ```bash
   git status
   git log --oneline --decorate --graph --max-count=5
   ```
3. Update your local main branch safely:
   ```bash
   git fetch origin
   git checkout main
   git pull --rebase
   ```
4. Reapply your work:
   ```bash
   git checkout <feature-branch>
   git rebase origin/main   # preferred
   # or, if necessary:
   # git merge origin/main
   ```
5. Resolve conflicts, rerun tests, then push:
   ```bash
   uv run pytest
   git push origin <feature-branch>
   ```

> **Important:** Never "stash, pull, push" blindly. Always review incoming changes and rerun tests before pushing.

### When You Truly Need to Stash
- Stash only if you must switch tasks:
  ```bash
  git stash push -m "WIP multi-model cleanup"
  ```
- When resuming:
  ```bash
  git stash pop
  uv run pytest   # re-verify before pushing
  ```

---

## 4. Post-Deployment Branch Management

1. After a successful production deploy, tag or branch the release:
   ```bash
   git checkout main
   git pull --ff-only
   git tag deploy-2025-10-24         # or create a release branch
   git push origin deploy-2025-10-24
   ```
2. Start new work from the updated `main` (or release branch) to avoid dragging stale history back in.

---

## Quick Reference

- **Push rejected?** Fetch → rebase/merge → resolve conflicts → rerun tests → push.
- **Service reachable but Railway fails health checks?** Confirm Hypercorn and Railway ports both use 8080.
- **Artifacts showing up in git?** Clean `.artifacts/`, `.ai_output/`, debug directories before committing.
- **Docs out of sync?** Verify behavior first, then update docs with "Last verified" timestamps.

Keep this checklist up to date as the deployment pipeline or tooling evolves.