# Waifu Virtual Try-On Backend (FastAPI)

**Last updated:** 2025-10-24

This service powers the virtual try-on experience. It orchestrates user uploads, costume metadata, and AI image generation. The backend is written in FastAPI and deployed on Railway with Python 3.13.

---

## Table of Contents

- [Waifu Virtual Try-On Backend (FastAPI)](#waifu-virtual-try-on-backend-fastapi)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
  - [Key Features](#key-features)
  - [Environment Configuration](#environment-configuration)
  - [Testing](#testing)
    - [Unit & Integration Tests (Mocked)](#unit--integration-tests-mocked)
    - [External AI Tests (Live NanoGPT API)](#external-ai-tests-live-nanogpt-api)
  - [AI Provider Notes](#ai-provider-notes)
  - [Debugging & Logs](#debugging--logs)
  - [Roadmap](#roadmap)
  - [Reference Docs](#reference-docs)

---

## Quick Start

```bash
# Install dependencies (requires uv)
uv sync

# Run the FastAPI app locally
uv run hypercorn main:app --reload --bind 0.0.0.0:8000
```

Health check endpoints:

- Root: `GET /`
- Health: `GET /healthz`

---

## Key Features

- **FastAPI + Hypercorn** runtime with dependency-injected services.
- **AI Provider Client** for NanoGPT models (`seedream-v4`, `google:4@1`, `qwen-image`, `gpt-image-1-mini`).
  - Client-level parallel helper for issuing multiple model requests concurrently.
  - Model-specific read timeouts with shared connect/write budgets.
  - Debug artifacts gated behind `AI_PROVIDER_DEBUG` and saved outside the repo.
  - Structured logging via the shared observability logger (`get_logger("ai_provider")`).
- **Catalog & Workflow Services** with Backblaze B2 storage integration.
- **Testing Strategy**
  - Unit tests with `pytest` and `httpx.MockTransport`.
  - Opt-in external tests marked with `@pytest.mark.external`.

---

## Environment Configuration

Create a `.env` or provide variables when launching:

```bash
DATABASE_URL=sqlite+aiosqlite:///./waifu.db
B2_KEY_ID=...
B2_APPLICATION_KEY=...
B2_BUCKET_ID=...
B2_DOWNLOAD_URL=https://cdn.example.com
B2_API_URL=https://api.backblaze.com
BACKGROUND_REMOVER_URL=https://bg.example.com
SEEDREAM_URL=https://seedream.example.com
GOOGLE_GENERATION_URL=https://google.example.com

AI_PROVIDER_URL=https://nano-gpt.com/v1/images/generations
AI_PROVIDER_API_KEY=sk-...

# Optional debugging controls
AI_PROVIDER_DEBUG=1
AI_DEBUG_DIR=/tmp/ai-debug
AI_OUTPUT_DIR=./.artifacts/ai
```

---

## Testing

### Unit & Integration Tests (Mocked)

```bash
uv run pytest tests/clients/test_ai_provider.py -v
uv run pytest
```

### External AI Tests (Live NanoGPT API)

```bash
AI_PROVIDER_API_KEY=... AI_PROVIDER_URL=... uv run pytest -m external -vv
```

- Tests are located in `tests/api/test_workflow_integration.py`.
- They require local fixture images (`tests/fixtures/test_images/*.jpeg`) and valid credentials.
- If prerequisites are missing, tests call `pytest.skip`.
- Generated assets are written to `.artifacts/ai/` (gitignored).

---

## AI Provider Notes

- `seedream-v4` and `google:4@1` accept costume URLs directly.
- `qwen-image` is supported but slow (2–3 minutes). `gpt-image-1-mini` is a faster alternative.
- The client enforces a 10 MB cap on downloaded reference assets.
- Parallel execution is currently limited to client-level helpers; workflow/API orchestration is planned.

For detailed guidance, see [`docs/features/multi-model-try-on.md`](docs/features/multi-model-try-on.md).

---

## Debugging & Logs

- Runtime logs flow through `src/observability/logger.get_logger("ai_provider")`, emitting structured JSON fields (model, status, latency, payload size).
- When `AI_PROVIDER_DEBUG=1`, detailed JSON traces are written to `AI_DEBUG_DIR` (defaults to system temp).
- Generated images from external tests land in `.artifacts/ai/`; clean them before committing.

---

## Roadmap

- Integrate multi-model orchestration into `WorkflowService`.
- Persist per-model results with a new `ModelResult` table.
- Add pytest hook for `--run-external` convenience flag.
- Expand automated coverage for parallel execution and error paths.

---

## Reference Docs

- [`docs/features/multi-model-try-on.md`](docs/features/multi-model-try-on.md)
- [`docs/testing/external-ai.md`](docs/testing/external-ai.md)
- [`docs/release-checklist.md`](docs/release-checklist.md)
- [`docs/storage/b2-object-naming.md`](docs/storage/b2-object-naming.md)
- [`docs/nano-gpt/image-generation.md`](docs/nano-gpt/image-generation.md)
- [`docs/multi-model-implementation-plan.md`](docs/multi-model-implementation-plan.md)

For planning guidelines, see `openspec/` instructions.