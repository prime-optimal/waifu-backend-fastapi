// docs/tasks/phase3-api-endpoints.md
# Phase 3 — API Endpoints & Schemas for Multi-Model Results

## Dependency
- **Requires:** Phase 2 (needs WorkflowService returning result list).

## Required .env Variables
Same as Phase 2 plus:
- `APP_ENV` *(if used for environment gating)*

## Tasks
1. **Schema Updates**
   - Update `WorkflowResponse` to include `results: list[ModelResultResponse]`.
   - Introduce new Pydantic model `ModelResultResponse`.

2. **Endpoint Additions**
   - Modify `POST /api/v1/workflows` to return enriched response.
   - Add `GET /api/v1/workflows/{workflow_id}/results` endpoint fetching from repository.

3. **Dependency Wiring**
   - Ensure FastAPI router imports new schema and uses dependency-injected WorkflowService.

4. **Backward Compatibility**
   - Maintain `final_asset_url` field but document deprecation in README.

## Tests to Mock / Execute
- `uv run pytest tests/api/test_workflow_integration.py::test_multi_model_success`
- `uv run pytest tests/api/test_workflow_integration.py::test_multi_model_partial_failure`
- `uv run pytest tests/api/test_workflow_integration.py::test_get_results_endpoint`
- `uv run pytest tests/api/test_main_app.py::test_openapi_schema` *(if applicable)*

## Notes
- Present changes via RepoPrompt MCP for review.
- Await architect approval before merge.
- Post-approval: run `uv run ruff check` and document in the journal.

## Workflow Expectations
1. Receive task document → review test list.
2. Stub tests/mocks as needed.
3. Implement feature.
4. Run unit/integration tests + lint.
5. Submit changes to RepoPrompt MCP for architectural review.
6. Address feedback, rerun tests.
7. After approval, apply real credentials/endpoints.
8. Complete `/docs/journal/<date>-<task>.md` entry following `JOURNAL.md`.