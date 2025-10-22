## 1. Implementation
- [x] 1.1 Establish FastAPI project structure, app factory, and shared settings management.
- [x] 1.2 Create Backblaze B2 client and storage abstractions for temporary folders and asset uploads.
- [x] 1.3 Build Postgres data access layer for costume metadata with daily refresh and manual sync triggers.
- [x] 1.4 Implement AI provider clients for background-remover, seedream-v4, and google:4@1 with consistent payload contracts.
- [x] 1.5 Wire REST endpoints for image upload, workflow orchestration, result retrieval, and user choice logging.
- [x] 1.6 Add workflow logging that stores prompts, model responses, and asset references in B2.

## 2. Validation
- [x] 2.1 Add unit tests for storage, database, and provider clients using mocks/fakes.
- [x] 2.2 Add integration tests covering the end-to-end generation workflow with stubbed external services.
