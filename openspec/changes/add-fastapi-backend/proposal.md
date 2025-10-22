## Why
Waifu Material needs a production-ready FastAPI backend to orchestrate costume try-on workflows, marshal AI providers, and persist assets so the React frontend can deliver generated renders reliably.

## What Changes
- Implement FastAPI endpoints for image upload, workflow orchestration, result retrieval, and preference logging.
- Integrate Backblaze B2 storage for temporary user uploads, generated images, and workflow logs.
- Connect to Neon/Postgres to source costume prompts, reference images, and affiliate metadata with daily refresh and manual sync support.
- Add AI provider clients for background-remover, seedream-v4, and google:4@1, including payload assembly with user and reference images.
- Introduce observability (structured logs/metrics) for tracing multi-step generation pipelines and external API calls.

## Process Requirements
- Use `uv` to manage packages, run scripts, and pin Python 3.13.
- Store API keys and provider URLs in `.env` files so builds and tests rely on environment variables.
- Require at least one associated test per task—preferably end-to-end—and ensure it passes before marking the task complete.
- Lint all code before submission and resolve all lint findings prior to completion.
- Create a new branch at the start of any task that delivers a new feature.
- Log completed tasks in `CHANGELOG.md` immediately after they are marked done.
- Keep individual files at or below 500 lines; refactor and add coverage if exceeding this limit.
- Write documentation after completing any new feature developed on a dedicated branch.

## Impact
- Affected specs: ai-generation-backend
- Affected code: main.py, src/api/, src/services/, src/clients/, tests/api/
