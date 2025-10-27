// docs/tasks/phase4-frontend-integration.md
# Phase 4 — Frontend Integration & End-to-End Validation

## Dependency
- **Requires:** Phase 3 (API contract stabilized).

## Parallelization
- Can start once Phase 2 is code-complete but must use final API shapes from Phase 3 before merging.

## Required .env Variables
Front-end devs need:
- `VITE_API_BASE_URL` (or equivalent)
- `VITE_AI_PREVIEW_BASE_URL` *(if used for proxies)*
Backend variables from Phase 2/3 must still be configured.

## Tasks
1. **API Client Updates**
   - Update frontend services to call:
     - `POST /api/v1/uploads`
     - `POST /api/v1/workflows`
     - `GET /api/v1/workflows/{id}/results` (poll or fetch once on completion).
   - Handle per-model status/asset display.

2. **UI Adjustments**
   - Render gallery/grid of model results with status badges.
   - Show fallback messaging if all models failed.

3. **Integration Testing**
   - Ensure `.env` or `.env.local` matches backend settings.
   - End-to-end flow against staging environment once backend approved.

## Tests to Mock / Execute
- Frontend unit tests (e.g., `pnpm test -- --watch=false SampleComponent.spec.ts`).
- Storybook visual check – render multi-model result list.
- Manual E2E script:
  - Upload image → run workflow → fetch results → verify assets + error handling.
- Backend regression: `uv run pytest tests/api/test_workflow_integration.py -vv`.

## Notes
- Use RepoPrompt MCP to review API contracts if uncertain.
- Task sign-off requires architect approval plus dev journal log.
- Coordinate with backend dev to obtain API keys/test accounts before “real” run.

## Workflow Expectations
1. Receive task document → review test list.
2. Stub tests/mocks as needed.
3. Implement feature.
4. Run unit/integration tests + lint.
5. Submit changes to RepoPrompt MCP for architectural review.
6. Address feedback, rerun tests.
7. After approval, apply real credentials/endpoints.
8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.