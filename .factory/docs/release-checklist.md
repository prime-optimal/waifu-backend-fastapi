# Release & Deployment Checklist

**Last updated:** 2025-10-24

Use this checklist before shipping changes to production or merging into `main`. It covers local validation, Railway deployment verification, and safe Git workflows—especially when a push is rejected because the remote branch has moved.

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
   # Optional: live tests (require credentials)
   AI_PROVIDER_API_KEY=... AI_PROVIDER_URL=... uv run pytest -m external -vv
   ```
3. **Lint / format**
   ```bash
   uv run ruff check
   ```
4. **Repo hygiene**
   - Ensure `.artifacts/`, `.ai_output/`, and debug dumps are ignored or cleaned.
   - Confirm generated images (e.g., from external tests) are not staged.
5. **Docs & changelog**
   - Update documentation **after verifying** the behavior they describe.
   - Add a "Last verified" stamp where relevant.

---

## 2. Railway Deployment Checks

1. **railpack.json**
   - Confirm the Hypercorn command binds to the expected port:
     ```json
     "startCommand": "uv run hypercorn main:app --bind 0.0.0.0:8080"
     ```
   - Ensure the `PORT` environment variable still matches (`8080`).
2. **Railway service settings**
   - Inbound HTTP port set to `8080`.
   - Environment variables (B2, AI provider, DB URL) match the docs.
3. **Smoke test (after deploy)**
   ```bash
   curl -I https://<railway-domain>/healthz
   ```
   Expect `200 OK`.

---

## 3. Safe Git Workflow

### When Ready to Commit
1. `git status` – verify only intended files are staged.
2. Write descriptive commit messages.

### If `git push` Is Rejected
1. **Pause** – do **not** immediately `git stash` and `git pull`.
2. Review your local state:
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
   git checkout <your-branch>
   git rebase origin/main   # preferred
   # or, if necessary:
   # git merge origin/main
   ```
5. If conflicts arise, resolve them carefully, run tests again, and only then push:
   ```bash
   git status
   uv run pytest
   git push origin <your-branch>
   ```

> **Important:** Do not stash, pull, and push within seconds. Always inspect incoming changes, resolve conflicts deliberately, and rerun tests before pushing.

### When You Truly Need to Stash
- Stash only if you must switch tasks:
  ```bash
  git stash push -m "WIP multi-model cleanup"
  ```
- When you’re ready to resume:
  ```bash
  git stash pop
  uv run pytest   # re-verify after conflicts are resolved
  ```

---

## 4. Post-Deployment Branch Management

1. After a successful production deployment, create a marker branch or tag:
   ```bash
  git checkout main
   git pull --ff-only
   git tag deploy-2025-10-24   # or
   git checkout -b release/2025-10-24
   git push origin release/2025-10-24
   ```
2. Use the branch/tag to roll back quickly if needed.
3. Begin new work on a fresh feature branch off the updated `main`.

---

### Quick Reference

- **Push rejected?** Fetch → rebase/merge → resolve → retest → push. Never "stash, pull, push" blindly.
- **Deployment port mismatch?** Check `railpack.json` and Railway’s HTTP port; Hypercorn must bind to the same port the platform expects.
- **Artifacts showing up in git?** Clean `.artifacts/`, `.ai_output/`, and any debug directories before committing.
- **Docs lagging behind code?** Update them only after verifying behavior; include "Last verified" dates.

Keep this checklist close to avoid last-minute surprises and broken builds. Update the document whenever the deployment pipeline or tooling changes.