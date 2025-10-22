## Context
The frontend needs a FastAPI backend that coordinates multi-step costume try-on workflows. The backend must accept a user selfie, retrieve costume prompts and reference imagery from Postgres, invoke background-remover followed by seedream-v4 and google:4@1 models, and persist all intermediate and final assets to Backblaze B2. The service also has to surface manual and scheduled costume catalog refreshes and log user feedback on preferred outputs.

## Goals / Non-Goals
- Goals: Deliver orchestrated workflow endpoints, abstract external providers with retry/backoff, ensure asset persistence in B2, and expose catalog sync controls backed by Postgres.
- Non-Goals: Replace the existing Bun API, implement frontend syncing logic, or build long-running queues beyond what FastAPI/background tasks can support initially.

## Decisions
- Decision: Use FastAPI dependency injection with a central settings object wired from environment variables for B2, Postgres, and AI provider credentials; keeps configuration explicit and testable.
- Decision: Model external providers through async client classes exposing idempotent `generate()` / `remove_background()` methods so they can be stubbed in tests and swapped if APIs change.
- Decision: Store workflow artifacts in B2 under `tmp/{user_session}/{timestamp}/` prefixes with structured JSON logs to aid debugging and future training pipelines.
- Decision: Run catalog refresh as a background task triggered either on schedule (via APScheduler/BackgroundTasks) or manual endpoint, writing fresh costume rows into Postgres with upsert semantics.

## Alternatives Considered
- Serverless functions per provider call were rejected due to coordination complexity and the need for shared storage writes across steps.
- Dedicated task queue (e.g., Celery) deferred until throughput demands exceed FastAPI background task capabilities; instrumentation will surface when we need to revisit.

## Risks / Trade-offs
- Risk: Long-running AI calls could block workers; mitigate by using async HTTP clients with timeouts and queuing background steps when possible.
- Risk: B2 availability issues might break workflows; introduce graceful degradation with local temporary storage fallback and retry policies.
- Risk: Growing costume dataset could slow refresh; plan to batch updates and cache JSON snapshots for the frontend.

## Migration Plan
1. Scaffold FastAPI app with configuration and health check.
2. Implement B2, Postgres, and AI clients with synthetic tests.
3. Add workflow endpoints behind feature flag so they can be exercised before exposing publicly.
4. Deploy behind staging environment, validate with sample costumes, then enable manual syncs.

## Open Questions
- Precise payload schemas for each AI provider (fields, limits) need confirmation.
- Expected size constraints for user uploads and reference images must be finalized.
- Authentication/authorization strategy for API endpoints remains to be defined.
