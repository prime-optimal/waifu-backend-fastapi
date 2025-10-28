# Next Steps Plan - 2025-10-25

**Created:** 2025-10-24 (Evening)
**Target completion:** Next 1-2 work sessions

---

## Overview

Phase 1 (AI Provider Client foundation) is 96% complete. The only remaining item is retry/backoff strategy, which is medium priority. The bigger opportunity is to start Phase 2 work (database schema + workflow integration) to unblock the end-to-end multi-model feature.

---

## Immediate Priorities (Tomorrow)

### Priority 1: Database Schema Extension (Task 2)
**Effort:** 2-3 hours
**Impact:** Unblocks workflow integration 

#### Subtasks:
1. **Design ModelResult table** (`src/db/models.py`)
   - Fields: `id`, `workflow_run_id` (FK), `model_name`, `asset_url`, `status`, `error_reason`, `processing_time_ms`, `created_at`
   - Index on `workflow_run_id` for fast lookups
   - Consider nullable `asset_url` for failed generations

2. **Create migration strategy**
   - Since there are no Alembic migrations yet, decide:
     - Option A: Introduce Alembic now (recommended for production)
     - Option B: Write manual SQL migration script
     - Option C: Use SQLAlchemy `create_all()` for new tables (acceptable for early stage)
   - Document the chosen approach in `docs/database-troubleshooting.md`

3. **Extend WorkflowRepository** (`src/db/repositories/workflows.py`)
   - Add `create_model_result()` method
   - Add `get_model_results_by_workflow()` method
   - Add tests to `tests/db/test_workflow_repository.py` (create if needed)

4. **Update existing data handling**
   - Keep `workflow_runs.final_asset_url` for backward compatibility
   - Plan migration path for existing runs (can backfill later)

**Success criteria:**
- New table exists in dev/test databases
- Repository methods tested with both success and failure cases
- Documentation updated with schema diagram

---

### Priority 2: Code Quality Improvements
**Effort:** 1 hour
**Impact:** Medium (improves maintainability)

#### Subtasks:
1. **Implement retry/backoff for AI Provider Client**
   - Use `tenacity` library (already in common FastAPI stacks) or roll simple exponential backoff
   - Retry only on transient errors (timeouts, 5xx responses)
   - Max 3 retries with exponential backoff (1s, 2s, 4s)
   - Add tests for retry behavior

2. **Error handling refinement** (Optional)
   - Decide: should unexpected exceptions bubble up or return `status="failed"`?
   - Current behavior is defensive (always returns result); consider logging improvement instead

**Success criteria:**
- Retry logic tested with mock transports simulating failures
- Documentation updated in `docs/features/multi-model-try-on.md`

---

## Phase 2 Preview Work (If Time Permits)

### Task: Basic Workflow Integration Spike
**Effort:** 1-2 hours (exploratory)
**Impact:** Validates approach before full implementation

#### Subtasks:
1. **Read and understand current WorkflowService** (`src/services/workflow.py`)
   - Map out current single-model flow: BackgroundRemover → Seedream → Google
   - Identify where to inject multi-model execution

2. **Sketch multi-model orchestration**
   - Option A: Replace Seedream+Google steps with AIProviderClient parallel calls
   - Option B: Keep existing flow as "legacy" and add new `multi_model_workflow()` method
   - Consider: how to handle partial failures (2 models succeed, 1 fails)

3. **Draft service method signature**
   ```python
   async def run_multi_model_workflow(
       self,
       *,
       session_id: str,
       costume_id: UUID,
       uploaded_asset_url: str,
       models: list[str] = ["seedream-v4", "google:4@1"],
   ) -> MultiModelWorkflowResult:
       ...
   ```

4. **Update B2 storage plan**
   - Ensure naming convention aligns with `docs/storage/b2-object-naming.md`
   - Plan uploads for each model: `workflows/{id}/model/{model_name}/01.png`

**Success criteria:**
- Clear decision documented: extend existing service vs new service
- Rough implementation plan in `docs/multi-model-implementation-progress.md`
- No actual code changes yet (just design/planning)

---

## Testing Strategy for Tomorrow

1. **Run full test suite before starting**
   ```bash
   uv run pytest
   ```
   Expected: 23 tests pass

2. **Run tests after each subtask**
   - Database changes: `uv run pytest tests/db/ -v`
   - Client changes: `uv run pytest tests/clients/test_ai_provider.py -v`

3. **Optional: Run external tests if working on retry logic**
   ```bash
   AI_PROVIDER_API_KEY=... uv run pytest -m external -vv
   ```

4. **Lint before committing**
   ```bash
   uv run ruff check
   ```

---

## Documentation Updates After Tomorrow's Work

Update these files after completing tasks:

1. **CHANGELOG.md** - Add entry for 2025-10-25
2. **docs/multi-model-implementation-progress.md** - Update Phase 2 status
3. **docs/multi-model-implementation-plan.md** - Mark Task 2 complete (if finished)
4. **docs/application-architecture.md** - Add ModelResult table to schema diagram (if applicable)

---

## Risk Mitigation

### Risk: Database migration complexity
- **Mitigation:** Start with SQLAlchemy `create_all()` for new tables, defer Alembic to later
- **Fallback:** Manual SQL script if SQLAlchemy approach has issues

### Risk: Workflow service changes break existing tests
- **Mitigation:** Run existing workflow integration tests frequently during changes
- **Fallback:** Add new methods rather than modifying existing ones

### Risk: Time overrun on database work
- **Mitigation:** If Task 2 takes >3 hours, pause and document progress, move to retry logic instead
- **Goal:** Make incremental progress, not perfect implementation

---

## Definition of Done for Tomorrow

**Minimum (must achieve):**
- [ ] ModelResult table exists and is tested
- [ ] WorkflowRepository can persist model results
- [ ] All existing tests still pass
- [ ] Documentation updated

**Stretch goals:**
- [ ] Retry logic implemented and tested
- [ ] Workflow integration design documented
- [ ] Phase 2 progress updated to "In Progress"

---

## Next Session After Tomorrow

If Task 2 (Database Schema) completes successfully tomorrow, the next session should tackle:

1. **Task 3: Service Orchestration**
   - Implement multi-model workflow method
   - Integrate AIProviderClient into WorkflowService
   - Handle partial failures and aggregate status

2. **Task 4: API Layer**
   - Create new endpoint or extend existing `/api/v1/workflows`
   - Return gallery-style response with per-model results

This would move the feature from "client foundation" to "functional prototype" stage.

---

## Questions to Resolve Tomorrow

1. **Migration strategy:** Alembic, manual SQL, or create_all()?
2. **Workflow integration:** Extend existing service or create new TryOnService?
3. **Backward compatibility:** Keep old flow or migrate everything to multi-model?
4. **Error handling:** Current defensive approach or bubble exceptions?

Document answers in the progress file as decisions are made.

---

**End of plan - ready for execution on 2025-10-25**
