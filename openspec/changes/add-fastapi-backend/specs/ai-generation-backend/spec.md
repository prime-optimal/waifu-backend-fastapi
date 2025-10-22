## ADDED Requirements
### Requirement: Image Upload Ingestion
The FastAPI backend SHALL accept a user-uploaded selfie along with a costume identifier and persist the original asset to a Backblaze B2 temporary folder.

#### Scenario: Upload accepted
- **WHEN** the frontend submits a valid authenticated request containing an image file and costume id
- **THEN** the backend stores the image under `tmp/{workflow}/original/` in B2 and returns a workflow identifier with acceptance metadata.

### Requirement: Background Removal Processing
The backend SHALL invoke the background-remover model against the stored user image before triggering costume generation workflows.

#### Scenario: Background removal succeeds
- **WHEN** a workflow advances past ingestion
- **THEN** the backend requests background removal, persists the result under `tmp/{workflow}/bg-removed/`, and records provider latency and status in the workflow log.

### Requirement: Costume Metadata Synchronization
The backend SHALL source costume prompts, reference image URIs, and affiliate metadata from Postgres with automatic refresh every 24 hours and a manual sync endpoint.

#### Scenario: Scheduled sync refreshes catalog
- **WHEN** 24 hours have elapsed since the prior sync
- **THEN** the backend refresh task upserts costume metadata from Postgres into the application cache and notes the sync timestamp.

#### Scenario: Manual sync succeeds
- **WHEN** an authorized user calls the manual sync endpoint
- **THEN** the backend re-reads costume data from Postgres, updates the cache, and responds with the number of records refreshed.

### Requirement: Multi-Model Costume Generation
The backend SHALL submit generation requests to both seedream-v4 (total 10 images including the user image) and google:4@1 (total 4 images including the user image) using the costume prompt and reference imagery.

#### Scenario: Dual model generation
- **WHEN** background removal is completed for a workflow
- **THEN** the backend assembles the prompt plus required reference images and dispatches concurrent requests to seedream-v4 and google:4@1, recording provider job ids and statuses.

### Requirement: Workflow Asset Persistence and Logging
The backend SHALL persist all intermediate assets, final renders, and a structured JSON log containing prompts, provider responses, and timing metadata within the workflow’s B2 folder.

#### Scenario: Workflow completion persisted
- **WHEN** both generation requests complete successfully
- **THEN** the backend stores each generated image under `tmp/{workflow}/outputs/{model}/`, writes a JSON workflow log, and marks the workflow status as complete.

### Requirement: User Preference Recording
The backend SHALL offer an endpoint for the frontend to submit which generated image a user prefers and store the selection alongside the workflow log.

#### Scenario: Preference stored
- **WHEN** the user submits their preferred model output referencing the workflow id
- **THEN** the backend records the choice in Postgres (or designated analytics store) and updates the B2 log file with the preference metadata.
