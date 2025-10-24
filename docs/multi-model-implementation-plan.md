# Multi-Model Try-On Feature Implementation Plan

**Last verified:** 2025-10-24

> This plan captures the intended end-to-end rollout for the multi-model try-on effort. Only the client-level foundation has landed so far. Refer to [docs/features/multi-model-try-on.md](features/multi-model-try-on.md) for the current live capabilities.

## Objective
Deliver a single workflow that can produce multiple costume renders from one user upload by coordinating several NanoGPT models, persisting per-model outcomes, and returning a gallery-style API response.

---

## Phase 1 – Foundation

### Task 1: AI Provider Client ▶️ **Mostly Complete (13/16 items done)**
**File:** `src/clients/ai_provider.py`

- ✅ Async client aligned with NanoGPT API (model selection, references array, auth headers)
- ✅ Model-specific timeouts and optional parallel helper (`generate_try_on_parallel`)
- ✅ Debug gating via `AI_PROVIDER_DEBUG` and `AI_DEBUG_DIR`
- ✅ **12 dedicated unit tests** in `tests/clients/test_ai_provider.py` with mock transports
- ❌ Structured logging via `observability.get_logger` (still using standard `logging`)
- ❌ ServiceError-only propagation (broad `except Exception` remains, returns status="failed")

**Next actions**
- Swap logger wiring to `get_logger("ai_provider")` and emit structured fields
- Revisit error handling to bubble unexpected exceptions (ServiceError/ValueError)

### Task 2: Database Schema (ModelResult table) ⏳ **Pending**
**Files:** `src/db/models.py`, `src/db/repositories/workflows.py`, migration scripts

- Introduce `model_results` table keyed to workflow runs
- Migrate existing `workflow_runs.final_asset_url` data
- Add repository helpers for upsert/query of per-model results

### Task 3: Service Orchestration ⏳ **Pending**
**File (planned):** `src/services/try_on.py` or extension to `WorkflowService`

- Coordinate multi-model execution (sequential or parallel)
- Handle partial failures and aggregate status
- Invoke storage uploads for successful outputs
- Emit structured logs/metrics for each invocation

### Task 4: API Layer ⏳ **Pending**
**File (planned):** `src/api/routes/try_on.py`

- Expose `/api/v1/try-on` endpoint with request validation
- Return gallery response containing model statuses and asset URLs
- Add OpenAPI models and rate limiting hooks
- Update `src/app/factory.py` to include the new router

---

## Phase 2 – Configuration & Testing

### Task 5: Application Settings ⏳ **Pending**
**File:** `src/app/settings.py`

- Expand model configuration (`ai_models`, `default_models`)
- Add feature flag (e.g., `multi_model_try_on_enabled`)
- Provide helpers to parse JSON/CSV environment overrides

### Task 6: Test Fixtures ⏳ **Pending**
**Files:** `tests/fixtures/test_costumes.json`, `tests/conftest.py`

- Prepare lightweight costume prompts/references
- Mock external HTTP calls where possible to avoid hitting real APIs

### Task 7: Automated Tests ⏳ **Pending**
**Files (planned):**
- `tests/services/test_try_on.py`
- `tests/api/test_try_on.py`
- `tests/clients/test_ai_provider.py` (new cases)

**Scenarios**
- Happy path for single and multi-model runs
- Partial failure handling
- Storage upload coordination
- Validation errors for unsupported models or missing inputs

---

## Phase 3 – Integration & Operations

### Task 8: Dependency Wiring ⏳ **Pending**
**Files:** `src/app/dependencies.py`, `src/app/factory.py`

- Register TryOn service and routers
- Ensure dependency overrides exist for tests

### Task 9: Storage Coordination ⏳ **Pending**
**Files:** `src/storage/b2.py`, environment configuration

- Confirm upload helpers support multi-file batches
- Add clean-up strategy for failed runs

### Task 10: Observability & Runbooks ⏳ **Pending**
- Switch AI client logging to shared observability logger
- Capture latency/error metrics per model
- Document live-test procedures in ops runbooks

---

## Testing Strategy (Current Reality)

| Scope                    | Location                                   | Status        | Notes                                                                 |
|--------------------------|--------------------------------------------|---------------|-----------------------------------------------------------------------|
| AI client unit tests     | `tests/clients/test_ai_provider.py`        | ✅ 12 tests    | Covers URLs, base64, parallel execution, error paths                  |
| Workflow integration     | `tests/api/test_workflow_integration.py`   | ✅ Existing   | Uses stubs; external API calls guarded by `@pytest.mark.external`     |
| Live provider tests      | `tests/api/test_workflow_integration.py`   | ✅ Available  | Run with `uv run pytest -m external`; skipped without credentials     |

---

## Success Criteria
- Workflow/API can request multiple models and persist each result
- Partial failures surface clearly in API responses and stored data
- Images and logs land outside the repository (B2 + debug dirs)
- Tests cover orchestration, error paths, and configuration edge cases
- Documentation reflects implemented behavior at each milestone

Once these checkpoints are complete, the feature can progress to rollout planning (feature flagging, UX updates, and operational readiness).
