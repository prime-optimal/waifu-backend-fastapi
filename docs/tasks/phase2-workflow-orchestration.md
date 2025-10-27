// docs/tasks/phase2-workflow-orchestration.md
# Phase 2 — WorkflowService Multi-Model Orchestration

## Dependency
- **Requires:** Phase 1 (ModelResult table & repo methods must exist).

## Parallelization
- Can run concurrently with Phase 5 (doc cleanup) after initial review, but complete before Phase 3.

## Required .env Variables
- `DATABASE_URL` or `NEON_DATABASE_URL`
- `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_ID`, `B2_DOWNLOAD_URL`
- `BACKGROUND_REMOVER_URL`
- `AI_PROVIDER_URL`
- `AI_PROVIDER_API_KEY`
- `AI_PROVIDER_DEBUG` *(optional for dev diagnostics)*
- `AI_PROVIDER_MODELS` *(optional CSV list; default `seedream-v4,google:4@1`)*

## Tasks
1. **Introduce AIProviderClient dependency**
   - Wire into `WorkflowService` (constructor & `from_settings`).
   - Ensure `close()` method shuts it down.

2. **Refactor `start_workflow`**
   - Run background removal once.
   - Call `generate_try_on_parallel` for configured models with basic retry/backoff (1s/2s/4s).
   - Persist each result via `create_model_result`.
   - Upload assets per-model to B2 using `workflows/{workflow_id}/models/{model_name}/result.png`.
   - Set workflow “hero” asset = first successful model (still store in `final_asset_url` for backwards compatibility).
   - Handle partial failures gracefully; mark workflow failed only if all models fail.

3. **Log Payload Updates**
   - Include array of per-model result metadata (status, URLs, error messages).

4. **Update `WorkflowState` dataclass**
   - Add `results: list[ModelResultDTO]` (new dataclass).
   - Include `primary_asset_url` alias for final asset.

## Tests to Mock / Execute
- `uv run pytest tests/services/test_workflow_service.py -k multi_model` *(to be created)*
  - Cases: both success, partial failure, total failure.
- `uv run pytest tests/storage/test_b2_storage.py` (ensure unchanged behavior).
- `uv run pytest tests/clients/test_ai_provider.py -k parallel`

## Notes
- Run MCP check via RepoPrompt before PR.
- Architect approval required before merging.
- Update journal entry after acceptance.

## Workflow Expectations
1. Receive task document → review test list.
2. Stub tests/mocks as needed.
3. Implement feature.
4. Run unit/integration tests + lint.
5. Submit changes to RepoPrompt MCP for architectural review.
6. Address feedback, rerun tests.
7. After approval, apply real credentials/endpoints.
8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.