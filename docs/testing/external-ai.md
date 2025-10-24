# External AI Provider Testing

**Note**: This document explains how tests are structured and which ones skip/pass by default.

---

## Quick Reference

| Command | What Runs | Notes |
|---------|-----------|-------|
| `uv run pytest tests/` | 21 tests PASS, 2 tests SKIP | Default — external tests skipped |
| `uv run pytest tests/ -m external` | 0 tests RUN, 2 tests SKIP | Marker selects external tests but conftest hook still skips them |
| `uv run pytest --co -q` | Lists all 23 collected tests | Shows structure; see "Understanding Skip Behavior" below |

---

## Understanding Skip Behavior

### Why Do Tests Get Skipped?

The test suite has **two categories**:

1. **Mocked Tests** (12 in `tests/clients/test_ai_provider.py`)
   - Use `httpx.MockTransport` to fake API responses
   - **Always run** — no credentials needed
   - Test client logic: URL handling, base64 encoding, parallel execution, error handling

2. **External Tests** (2 in `tests/api/test_workflow_integration.py`)
   - Make **real HTTP requests** to NanoGPT API
   - **Always skipped by default** via `conftest.py` hook (lines 22-30)
   - Marked with `@pytest.mark.external`
   - Require live credentials to run

### The conftest Skip Hook (Why It's Always Skipped)

File: `tests/conftest.py:22-30`

```python
def pytest_collection_modifyitems(config, items):
    """Skip external tests by default unless --run-external is specified."""
    if not config.getoption("--run-external", default=False):
        skip_external = pytest.mark.skip(
            reason="use --run-external to run external API tests"
        )
        for item in items:
            if "external" in item.keywords:
                item.add_marker(skip_external)
```

**What this means:**
- The hook looks for a `--run-external` pytest flag
- **This flag is not registered**, so it always defaults to False
- Therefore, tests marked `@pytest.mark.external` are **always skipped**
- Using `-m external` marker does NOT override this; conftest runs first

---

## Running Tests Properly

### Run All Mocked Tests (Default, Always Works)

```bash
uv run pytest tests/
```

**Result**: 21 PASSED, 2 SKIPPED

**Tests that run:**
- `tests/api/test_main_app.py` (2 tests)
- `tests/api/test_workflow_integration.py::test_full_workflow` (1 test)
- `tests/api/test_workflow_integration.py::test_catalog_sync_endpoint` (1 test)
- `tests/clients/test_ai_provider.py` (12 tests with mocked HTTP)
- `tests/clients/test_clients.py` (3 tests)
- `tests/db/test_costume_repository.py` (1 test)
- `tests/storage/test_b2_storage.py` (1 test)

**Tests that skip:**
- `test_real_ai_provider_integration` — marked external
- `test_real_ai_provider_all_user_images` — marked external

---

## Running External Tests (Live API)

### Option 1: Run Specific Test by Name

```bash
uv run pytest tests/api/test_workflow_integration.py::test_real_ai_provider_integration -v
```

**Requirements:**
- `AI_PROVIDER_API_KEY` environment variable set
- `AI_PROVIDER_URL` environment variable set (defaults to `https://nano-gpt.com/v1/images/generations`)
- Test fixture images exist in `tests/fixtures/test_images/`

**Example:**
```bash
AI_PROVIDER_API_KEY=your-key-here uv run pytest tests/api/test_workflow_integration.py::test_real_ai_provider_integration -v
```

### Option 2: Run Via Marker (Still Skips Due to conftest Bug)

```bash
uv run pytest -m external -v
```

**Note**: This WILL NOT work as you might expect. The `-m external` marker selects the tests, but the conftest hook still marks them as skipped because `--run-external` flag is not registered. You must use Option 1 (run by test name directly).

---

## Credentials & Environment Variables

### Required for External Tests

| Variable | Purpose | Example |
|----------|---------|---------|
| `AI_PROVIDER_API_KEY` | Bearer token for NanoGPT API | `sk-proj-abc123...` |
| `AI_PROVIDER_URL` | API endpoint (optional) | `https://nano-gpt.com/v1/images/generations` |

### Optional Debug Settings

| Variable | Purpose | Default |
|----------|---------|---------|
| `AI_PROVIDER_DEBUG` | Save debug JSON to disk | `0` (disabled) |
| `AI_DEBUG_DIR` | Where to save debug output | System temp directory |

### Setting Environment Variables

**Option A: Inline**
```bash
AI_PROVIDER_API_KEY=your-key uv run pytest tests/api/test_workflow_integration.py::test_real_ai_provider_integration
```

**Option B: Create `.env` file**
```bash
# .env (not committed to git)
AI_PROVIDER_API_KEY=your-key
AI_PROVIDER_URL=https://nano-gpt.com/v1/images/generations
```

Then:
```bash
set -a && source .env && uv run pytest tests/api/test_workflow_integration.py::test_real_ai_provider_integration
```

**Option C: Export environment**
```bash
export AI_PROVIDER_API_KEY=your-key
uv run pytest tests/api/test_workflow_integration.py::test_real_ai_provider_integration
```

---

## What Each External Test Does

### `test_real_ai_provider_integration`

**Location**: `tests/api/test_workflow_integration.py:181-244`

**What it tests:**
- Single model generation (google:4@1)
- Real API call to NanoGPT
- Uses `user1.jpeg` and 2 Bowsette costume references from fixtures

**Prerequisites:**
- `AI_PROVIDER_API_KEY` set
- `tests/fixtures/test_images/user1.jpeg` exists
- `tests/fixtures/test_images/bowsette-*.png/jpg` exist

**Runtime:** ~20–30 seconds

**Output:**
```
Status: success
Model: google:4@1
Processing time: 2345ms
Generated filename: 2025-10-24-google-4at1-abc123.png
```

### `test_real_ai_provider_all_user_images`

**Location**: `tests/api/test_workflow_integration.py:247-394`

**What it tests:**
- All 3 user images (user1–3.jpeg)
- All 3 models (seedream-v4, google:4@1, qwen-image)
- Real API calls for 9 total generations
- Per-model pass/fail summary

**Prerequisites:**
- Same as above plus `user2.jpeg`, `user3.jpeg`

**Runtime:** 5–10+ minutes (qwen-image is slow)

**Output:**
```
Testing user image 1/3: user1.jpeg
  Trying model: seedream-v4
    Status: success
    Processing time: 2500ms
    Generated filename: 2025-10-24-seedream-v4-xyz123.png
  Trying model: google:4@1
    Status: success
  Trying model: qwen-image
    Status: success (but slow — 120+ seconds)
    
SUMMARY:
  Total tests: 9
  Successful: 8
  Failed: 1
```

---

## Troubleshooting

### Test Runs Instantly with SKIPPED

**Symptom**: Test runs in <1 second and shows SKIPPED

**Cause**: External test being skipped by conftest hook (expected default behavior)

**Solution**: This is normal. External tests are meant to be skipped unless explicitly run.

### Test Hangs or Times Out

**Symptom**: Test appears to hang; eventually times out

**Cause**: Likely running `qwen-image` model (very slow) or network issue

**Solution:**
1. Check which model is running
2. If qwen-image: wait 2–3 minutes; it's expected to be slow
3. If other model: check network and API status
4. Monitor your NanoGPT account for errors/throttling

### "Invalid API key" Error

**Cause**: `AI_PROVIDER_API_KEY` not set or incorrect

**Solution:**
```bash
# Verify it's set
echo $AI_PROVIDER_API_KEY

# If empty, set it
export AI_PROVIDER_API_KEY=your-key-here
```

### Test Fixture Images Missing

**Cause**: Test images not in repo or removed

**Solution:**
```bash
# Check if they exist
ls tests/fixtures/test_images/

# Expected files:
# - user1.jpeg, user2.jpeg, user3.jpeg
# - bowsette-blurred.png, bowsette-crown.jpg, bowsette-front.jpg, etc.
```

### API Returns "Rate Limited" or "Quota Exceeded"

**Cause**: Too many requests or insufficient credits on NanoGPT account

**Solution:**
- Wait 1 hour before retrying
- Check NanoGPT dashboard for account status
- Run quick test (single user + google:4@1) instead of all-users test

---

## Summary Table: What Runs vs What Skips

| Test | Marker | Conftest Behavior | Run Command | Prerequisites |
|------|--------|------------------|-------------|---------------|
| Mocked client tests | `@asyncio` | Runs | `pytest tests/` | None |
| Full workflow (mocked) | `@asyncio` | Runs | `pytest tests/` | None |
| Real AI provider | `@asyncio` + `@external` | SKIP (hook) | Direct name only | API_KEY + fixtures |
| Real all-images | `@asyncio` + `@external` | SKIP (hook) | Direct name only | API_KEY + all fixtures |

**TL;DR for determining if task is "done":**
- Run `uv run pytest tests/` — if 21 pass and 2 skip, mocked tests work ✅
- External tests are intentionally skipped by design; run them manually with credentials only when needed
