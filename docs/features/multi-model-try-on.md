# Multi-Model Virtual Try-On

**Last verified:** 2025-10-24

## Overview

The multi-model virtual try-on capability currently consists of an enhanced AI provider client that can request images from multiple NanoGPT models using a single user upload. Orchestration at the workflow/API layer is planned but not yet implemented.

## Architecture

### Components

1. **AIProviderClient** (`src/clients/ai_provider.py`) — *Implemented*
   - Handles communication with the NanoGPT API
   - Supports seedream-v4, google:4@1, qwen-image, and gpt-image-1-mini models
   - Offers client-level parallel execution helpers and model-specific timeouts
   - Emits structured logs via the shared observability logger (`get_logger("ai_provider")`)

2. **Workflow Integration** (`src/services/workflow.py`) — *Planned*
   - Future work will integrate the client into the workflow service
   - Responsibilities include aggregating results, coordinating storage uploads, and persisting per-model metadata

3. **API Endpoints** (`src/api/routes/`) — *Planned*
   - New endpoints will expose multi-model generation once orchestration is in place
   - Current routes still operate on the legacy single-model workflow

## Supported Models

| Model            | Image Limit | Typical Processing Time | Notes                                                   |
| ---------------- | ----------- | ------------------------ | -------------------------------------------------------- |
| seedream-v4      | 10 images   | ~25–35 seconds           | Accepts direct URLs for costume references               |
| google:4@1       | 4 images    | ~20–30 seconds           | Accepts direct URLs; 1024x1024 output                    |
| qwen-image       | 4 images    | ~2–3 minutes             | Requires base64-encoded image data and longer timeouts   |
| gpt-image-1-mini | 4 images    | ~40–60 seconds           | Faster alternative when qwen-image latency is too high   |

## Usage (Client Level)

### Single Model Generation

```python
from src.clients.ai_provider import AIProviderClient

client = AIProviderClient(
    base_url="https://nano-gpt.com/v1/images/generations",
    api_key="your-api-key",
)

result = await client.generate_try_on(
    model_name="google:4@1",
    user_image_path="/path/to/user.jpg",
    costume_reference_urls=["https://example.com/costume.jpg"],
    prompt="Virtual try-on with the costume reference",
    seed=1001,
)
```

### Parallel Model Generation (Client Helper)

```python
results = await client.generate_try_on_parallel(
    model_names=["seedream-v4", "google:4@1"],
    user_image_path="/path/to/user.jpg",
    costume_reference_urls=["https://example.com/costume.jpg"],
    prompt="Virtual try-on with the costume reference",
    max_concurrent=2,
)
```

> **Note:** Parallel execution is currently limited to the client helper. Workflow/API layers still execute single-model flows.

## Input Formats

### User Image

- **File Path**: Local path converted to base64 before upload
- **Base64**: Provide an existing `data:image/...;base64,...` string
- **URL**: Direct HTTP/HTTPS URL (used as-is)

At least one of these must be provided.

### Costume References

- **URLs**: Preferred for seedream-v4 and google:4@1
- **File Paths**: Converted to base64
- **Base64**: Accepted for any model
- Automatically converted to base64 when qwen-image is selected

## Configuration

### Environment Variables

```bash
AI_PROVIDER_URL=https://nano-gpt.com/v1/images/generations
AI_PROVIDER_API_KEY=your-api-key

# Optional debug controls
AI_PROVIDER_DEBUG=1
AI_DEBUG_DIR=/tmp/ai-debug
AI_OUTPUT_DIR=./.artifacts/ai
```

### Model Settings

Configured in `src/app/settings.py`:

```python
ai_models = {
    "standard": "seedream-v4",
    "premium": "google:4@1",
    "fast": "qwen-image",
}
```

These settings are consumed by higher layers once integration work resumes.

## Error Handling

- HTTP errors from the provider raise `ServiceError`.
- Other exceptions result in an `AIProviderResult` with `status="failed"` and an `error_reason` string.
- Every result (success or failure) records `processing_time_ms` for diagnostics.

## Storage & B2 Naming

Backblaze B2 objects follow a workflow-centric prefix:

```
workflows/{workflow_id}/
  user/original.jpg
  costume/01-bowsette-reference.jpg
  costume/02-crown-reference.jpg
  model/seedream-v4/01.png
  model/google-4at1/01.png
  model/gpt-image-1-mini/01.png
  logs/try-on.json
```

- Prefixing keeps each user’s uploads and generated assets grouped.
- B2 retention is currently 7 days visible + 7 days hidden (14-day total window).
- Debug logs can be mirrored into `logs/` for auditing.
- See [`docs/storage/b2-object-naming.md`](../storage/b2-object-naming.md) for full guidance.

## Testing

### Unit & Integration Tests (Mocked)

```bash
uv run pytest tests/clients/test_ai_provider.py -v
```

These tests use stub transports and do **not** hit the live API.

### External Tests (Live API)

```bash
AI_PROVIDER_API_KEY=... AI_PROVIDER_URL=... uv run pytest -m external -vv
```

- Live tests reside in `tests/api/test_workflow_integration.py`.
- They require local fixture images and valid API credentials.
- If prerequisites are missing, tests call `pytest.skip`.

## Performance Considerations

- **Timeouts**: Connect/write timeouts are fixed at 10 seconds; read timeout varies by model (45s default, 90s for google:4@1/seedream-v4/gpt-image-1-mini, 180s for qwen-image).
- **Concurrency**: `generate_try_on_parallel` uses an `asyncio.Semaphore`; default `max_concurrent=3`.
- **Payload Size**: Costume downloads are capped at 10 MB per image to avoid runaway memory usage.

## Logging & Debugging

- Structured logs flow through `get_logger("ai_provider")`, emitting JSON fields for model, status, latency, and payload size.
- When `AI_PROVIDER_DEBUG=1`, structured JSON files are written to `AI_DEBUG_DIR` (default system temp).
- Debug artifacts and saved images are intentionally directed outside the repository to avoid git noise.

## Roadmap / Future Enhancements

- Integrate the client into `WorkflowService` with persistent `ModelResult` records.
- Expose multi-model API endpoints with gallery-style responses.
- Adopt pytest `--run-external` hook for cleaner live-test opt-in.
- Expand automated test coverage for error paths and parallel execution.
- Add caching or pre-processing for frequently used costume references.

For historical plans and design notes, see the multi-model implementation plan/progress documents; the feature status above reflects the codebase as of the last verification date.