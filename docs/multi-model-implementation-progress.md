# Multi-Model Try-On Implementation Progress

**Last verified:** 2025-10-24
**Current scope:** Client and tests complete; workflow/API integration pending. See [docs/features/multi-model-try-on.md](features/multi-model-try-on.md) for up-to-date behavior.

---

## Phase Snapshot

| Phase            | Status        | Notes                                                                 |
|------------------|---------------|-----------------------------------------------------------------------|
| Phase 1          | 95% Done      | AI client + 14 tests complete; logging/error handling need refinement |
| Phase 2          | Pending       | Configuration, fixtures, and workflow testing not yet started         |
| Phase 3          | Pending       | Service/router integration and observability work outstanding         |

---

## Phase 1: Foundation (Task 1)

### What's Done ✅
- `AIProviderClient` talks to NanoGPT, supports seedream-v4, google:4@1, qwen-image
- Optional parallel helper (`generate_try_on_parallel`) with semaphore control
- Per-model read timeouts plus shared connect/write limits
- Debug artifacts gated behind `AI_PROVIDER_DEBUG` and `AI_DEBUG_DIR`
- External integration tests marked with `@pytest.mark.external` and redirected to `.artifacts/ai`
- **12 unit tests** in `tests/clients/test_ai_provider.py` covering URLs, base64, parallel execution, errors
- `.artifacts/` is gitignored (line 18)

### What's Still Open
- Structured logging via `observability.get_logger` (still using standard `logging`)
- Raising typed exceptions instead of always returning `status="failed"`
- Skip logic (`--run-external`) for live tests (conftest hook references flag that isn't registered in pytest)

---

## External API Verification (Manual)

- Location: `tests/api/test_workflow_integration.py`
- Invocation:
  ```bash
  AI_PROVIDER_API_KEY=... AI_PROVIDER_URL=... uv run pytest -m external -vv
  ```
- Behavior: Tests skip when credentials or fixture images are missing. They remain manual/optional.

---

## Upcoming Work (Phase 1 Remainder)

1. **Logging:** Replace direct `logging.getLogger` usage with `get_logger("ai_provider")` and emit structured fields.
2. **Error Handling:** Bubble unexpected exceptions (ServiceError/ValueError) rather than always returning a failed result.
3. **Docs Update:** Keep changelog and status docs aligned with actual capabilities.

---

## Blockers / Risks

- Logging not yet integrated with observability stack.
- Live API tests still take several minutes and rely on manual credentials; they must remain opt-in.
- No persistence layer for per-model results yet, so workflow integration cannot proceed.

---

## Next Milestones

| Milestone | Target Outcome                                                    | Status         |
|-----------|-------------------------------------------------------------------|--------------------|
| M1        | Structured logging + refined error handling                       | Ready to start |
| M2        | Database schema extension (ModelResult)                           | Blocked on M1  |
| M3        | Try-on service + API endpoint wiring                              | Blocked on M2  |
| M4        | Full test suite (service + API + storage)                         | Blocked on M3  |

Keep this document in sync as milestones close or new blockers surface.
