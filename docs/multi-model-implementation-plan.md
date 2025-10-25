# Multi-Model Try-On Feature Implementation Plan

**Last verified:** 2025-10-24 (Evening)

> This plan captures the intended end-to-end rollout for the multi-model try-on effort. Only the client-level foundation has landed so far. Refer to [docs/features/multi-model-try-on.md](features/multi-model-try-on.md) for the current live capabilities.

## Objective
Deliver a single workflow that can produce multiple costume renders from one user upload by coordinating several NanoGPT models, persisting per-model outcomes, and returning a gallery-style API response.

---

## Phase 1 – Foundation

### Task 1: AI Provider Client ✅ **Complete (15/16 items)**
**File:** `src/clients/ai_provider.py`

- ✅ Async client aligned with NanoGPT API (model selection, references array, auth headers)
- ✅ Model-specific timeouts and optional parallel helper (`generate_try_on_parallel`)
- ✅ Debug gating via `AI_PROVIDER_DEBUG` and `AI_DEBUG_DIR`
- ✅ Structured logging via `observability.get_logger("ai_provider")`
- ✅ 12 dedicated unit tests in `tests/clients/test_ai_provider.py` with mock transports
- ✅ Download safeguards (10 MB cap, per-model read timeout budgets)
- ❌ Retry/backoff strategy for transient provider failures

**Next actions**
- Evaluate retry/backoff options for provider hiccups (exponential backoff or Polly-style retries)

### Task 2: Database Schema (ModelResult table) ⏳ **Pending**
**Files:** `src/db/models.py`, `src/db/repositories/workflows.py`, migration scripts

- Introduce `model_results` table keyed to workflow runs
- Migrate existing `workflow_runs.final_asset_url` data
- Add repository helpers for upsert/query of per-model results

### Task 3: Service Orchestration ⏳ **Pending**
**File (planned):** `src/services/try_on.py` or extension to `WorkflowService`

- Coordinate multi-model execution (sequential or parallel) and respect timeouts per model
- Handle partial failures and aggregate status
- Invoke storage uploads for successful outputs using the Backblaze naming convention ([docs/storage/b2-object-naming.md](storage/b2-object-naming.md))
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
**Files:** `tests/fixtures/`

- Extend costume and user-image fixtures to cover new models (e.g., `gpt-image-1-mini`)
- Add local storage stubs for B2 upload paths to ensure naming convention consistency
- Provide deterministic prompts for regression comparisons

### Task 7: External Test Harness ⏳ **Pending**
**Files:** `tests/api/test_workflow_integration.py`, `tests/conftest.py`

- Register a pytest option (`--run-external`) to gate live tests
- Capture per-model timing metrics in test logs via structured logging
- Create optional scripts to diff generated images across runs

---

## Phase 3 – Orchestration & Observability

### Task 8: Workflow Integration ⏳ **Pending**
**File:** `src/services/workflow.py` (or new `TryOnService`)

- Invoke multi-model generation, orchestrate storage uploads, persist results
- Store per-model metadata (status, asset URL, timing)
- Upload debug logs to B2 prefixed under `workflows/{workflow_id}/logs/`

### Task 9: API Response ⏳ **Pending**
**Files:** `src/api/routes/workflows.py` (or new try-on route)

- Return gallery payload including seeded results, failure reasons, and signed URLs
- Add pagination or filtering if multiple iterations are supported

### Task 10: Observability & Metrics ⏳ **Pending**
**Files:** `src/observability/`, dashboards

- Push structured logs to Logfire / Railway viewer (already instrumented at client level)
- Surface per-model timing, success rates, and error distribution
- Add alerting thresholds for timeouts or repeated provider failures

---

## Completion Criteria

The feature is complete when:

1. Workflow service orchestrates multiple models and persists each result.
2. API exposes a gallery response per workflow run.
3. B2 storage receives all assets/logs using the documented naming scheme.
4. Structured logging captures model metrics end-to-end (client → service → API).
5. Automated tests cover happy paths, error handling, and storage interactions.
6. Documentation (feature, testing, release notes) reflects the final behavior with up-to-date "Last verified" stamps.

Track progress in the accompanying progress and summary documents; update this plan as milestones are achieved.
