## Summary of Bloat & Redundancy

| Area                     | Problem                                                                                                                                                               | Action                                                                                                                                                                                                                                                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Documentation**        | 25+ overlapping planning docs, duplicate diagrams, stale roadmap items.                                                                                               | Keep only `README.md`, `docs/data-model/README.md`, `docs/features/multi-model-try-on.md`, `docs/testing/external-ai.md`, `docs/release-checklist.md`. Archive/delete all `multi-model-*`, `next-steps-*`, `nano-gpt/*`, `docs/database-*`, analytics/test summaries, and redundant diagrams that describe deferred work. |
| **Data Model**           | Schema includes unused MVP tables (`assets`, `processing_metrics`, `costume_popularity`). Missing minimal `model_results` table required for multi-model persistence. | Introduce lean `model_results` table; cease work on `assets`, `processing_metrics`, `costume_popularity` until v1.1. Update diagrams/doc text to reflect MVP entities only.                                                                                                                                               |
| **Service/DTO Diagrams** | Mermaid diagrams list planned DTOs (`WorkflowExecutionContext`, `AssetUploadRequest`, etc.) not backed by code.                                                       | Rewrite diagrams to show only existing or 24h MVP DTOs (`WorkflowState`, new `ModelResultDTO`). Remove analytics/service placeholders.                                                                                                                                                                                    |
| **API Contracts**        | Response models defined for endpoints that don't exist (analytics, detailed workflow view).                                                                           | Delete unused schema definitions and update UI model diagram to show only MVP responses plus new `ModelResultResponse`.                                                                                                                                                                                                   |

---

## Critical Path to Ship in 24 Hours

### 1. Database - Source Strategy for the 24‑Hour Ship Window
- **File**: `src/db/models.py` (lines near `WorkflowRun`, `Asset`)
  - Add `class ModelResult(Base)` with columns: `id`, `workflow_run_id` FK, `model_name`, `status` (reuse `WorkflowStatus` enum), `asset_url`, `error_message`, `processing_time_ms`, `created_at`.
  - Remove or comment relationships for unused tables if they remain to prevent accidental access; set `WorkflowRun.final_asset_url` comment noting “deprecated post multi-model”.
  - Add relationship `WorkflowRun.model_results = relationship("ModelResult", back_populates="workflow_run")`.
  - Add `ModelResult.workflow_run` relationship.
- **Settings**: ensure `Database.create_all()` includes new table—no migration framework in use.
- **Docs**: Update `docs/data-model/README.md` ERD to match trimmed schema; delete references to deferred tables.




### 2. Repository Layer
- **File**: `src/db/repositories/workflows.py`
  - Add import for `ModelResult`.
  - Extend repository with:
    ```python
    async def create_model_result(
        self,
        session: AsyncSession,
        *,
        workflow_run_id: uuid.UUID,
        model_name: str,
        status: WorkflowStatus,
        asset_url: str | None,
        error_message: str | None,
        processing_time_ms: int | None,
    ) -> ModelResult
    ```
    - Persist record; do not flush commit.
  - Add `async def get_model_results(...) -> list[ModelResult]` ordered by `created_at`.
  - Mark `mark_completed` to stop writing `seedream_asset_url`, `final_asset_url`; store top-level canonical final result by selecting “primary” model (see Workflow plan below).
  - Ensure existing callers updated to new signature.

### 3. Workflow Service Refactor
- **File**: `src/services/workflow.py`
  - **Dependencies**:
    - Inject `AIProviderClient` (new dependency) via constructor; add to `from_settings` by reading `settings.ai_provider_url` and `settings.ai_provider_api_key`. Confirm settings fields exist or add to `src/app/settings.py`.
    - Preserve `BackgroundRemoverClient` if still required for prompt prep.
  - **DTOs**:
    - Create internal dataclass `ModelResultDTO` (`model_name`, `status`, `asset_url`, `error_message`, `processing_time_ms`).
    - Update `WorkflowState` to include `primary_result_url: str` (former `final_asset_url`) and `results: list[ModelResultDTO]`.
  - **`start_workflow` logic**:
    1. Create `WorkflowRun` as today.
    2. Generate background image (unchanged).
    3. Build prompt(s)/references once per run.
    4. Call `AIProviderClient.generate_try_on_parallel` with targeted models (e.g., `["seedream-v4", "google:4@1"]`). Accept `model_name` list from settings if configurable.
    5. For each `AIProviderResult`, upload image to B2 using path pattern `f"{workflow_run_id}/models/{model}/result.png"` (derive from `settings.workflow_tmp_prefix` or new constant). Persist URL.
       - Wrap provider calls with retry helper (simple async loop with `asyncio.sleep` 1/2/4 seconds on `ServiceError`).
    6. Persist each outcome via new `create_model_result`.
    7. Select default hero asset: prefer first success in configured order; fallback to empty string.
    8. Populate log payload referencing per-model results rather than single google result.
    9. Update `mark_completed` call to pass `final_asset_url` = hero asset (for backwards compatibility) and store log path.
  - **Error handling**:
    - If all models fail, mark workflow failed (`mark_failed`) and raise HTTP 502.
    - If some succeed, still mark completed; include failure metadata in `ModelResultDTO`.
  - **Close method**: ensure AIProviderClient `close()` called (extend `WorkflowService.close`).
  - **Imports**: remove direct `SeedreamClient`/`GoogleGenerationClient` usage if replaced; otherwise adapt to use new client.

### 4. API Layer
- **File**: `src/api/routes/workflows.py`
  - Update `WorkflowResponse` to match new `WorkflowState` signature (`primary_result_url` renamed to `final_asset_url` for compatibility, include `results: list[ModelResultResponse]`).
  - Create new Pydantic model:
    ```python
    class ModelResultResponse(BaseModel):
        model_name: str
        status: WorkflowStatus
        asset_url: str | None
        error_message: str | None
    ```
  - Modify `/workflows` POST handler to return updated response with results list.
  - Add new endpoint `GET /workflows/{workflow_id}/results` that fetches via repository `get_model_results` and returns serialized list (front-end polling).
  - Ensure dependency injection uses `WorkflowService.get_workflow` returning new structure (update service method accordingly).

### 5. Settings & Dependency Wiring
- **File**: `src/app/settings.py`
  - Confirm presence of `ai_provider_url`, `ai_provider_api_key`, `ai_provider_models` (optional `list[str]` with default `["seedream-v4", "google:4@1"]`), `ai_provider_parallelism`.
  - If missing, add new fields with environment alias support.
- **File**: `src/app/factory.py`
  - Pass `AIProviderClient` to `WorkflowService.from_settings` (or instantiate inside).
  - Ensure `create_all()` still invoked to materialize `model_results`.

### 6. Frontend Contract Notes (for coordination)
- Provide interface spec: `/api/v1/workflows` response includes `results`; `/results` endpoint returns same payload.
- Document in README the new call sequence.

### 7. Documentation Cleanup
- Update `README.md` sections:
  - Remove roadmap items deferred to v1.1.
  - Add “Multi-model orchestration” bullet describing new endpoints and `results` array.
- Revise `docs/data-model/README.md` diagrams to remove `assets`, `processing_metrics`, `costume_popularity`, and planned DTO/API classes; highlight new `model_results`.
- `docs/features/multi-model-try-on.md`: refresh instructions to use `/workflows/{id}/results`.
- Delete redundant docs as per summary.

---

## Architectural Considerations & Impacts

1. **Backwards Compatibility**: `WorkflowResponse.final_asset_url` remains to support existing frontend code, but should now map to hero result. Document that clients must migrate to `results`.
2. **Concurrency & Retries**: Keep retry logic within WorkflowService to isolate provider flakiness; ensure B2 uploads only run for successful results.
3. **Performance**: `generate_try_on_parallel` already bounds concurrency; supply `max_concurrent` from settings if needed.
4. **Error Surfacing**: Partial failure scenario must not bubble as HTTP error; include errors per model to allow frontend messaging.
5. **Storage Naming**: Consolidate B2 prefixes to avoid reuse of deprecated `workflow_tmp_prefix` for final results (consider new `workflow_result_prefix` setting).
6. **Future Analytics**: By trimming schema now, later migrations must reintroduce analytics tables with separate revisions.

---

By executing the steps above—schema addition, repository extension, workflow service refactor with AI provider integration, updated API responses/endpoints, and targeted doc cleanup—the backend will expose the multi-model artifacts the frontend needs, eliminating current bloat while aligning documentation and architecture with the MVP that can be shipped within the next 24 hours.

<chatName="Implementation plan for multi-model MVP release"/>