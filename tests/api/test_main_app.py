import importlib
import sys

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def main_app(tmp_path, monkeypatch) -> FastAPI:
    env_values = {
        "DATABASE_URL": f"sqlite+aiosqlite:///{(tmp_path / 'main.db')}",
        "B2_KEY_ID": "key",
        "B2_APPLICATION_KEY": "secret",
        "B2_BUCKET_ID": "bucket",
        "B2_DOWNLOAD_URL": "https://cdn.test",
        "B2_API_URL": "https://api.test",
        "BACKGROUND_REMOVER_URL": "https://bg.test",
        "SEEDREAM_URL": "https://seedream.test",
        "GOOGLE_GENERATION_URL": "https://google.test",
    }
    for key, value in env_values.items():
        monkeypatch.setenv(key, str(value))

    sys.modules.pop("main", None)
    main = importlib.import_module("main")
    try:
        yield main.app
    finally:
        sys.modules.pop("main", None)


def test_main_includes_api_routes(main_app: FastAPI):
    paths = {route.path for route in main_app.routes if hasattr(route, "path")}
    assert "/" in paths
    assert "/healthz" in paths
    assert "/api/v1/uploads" in paths
    assert "/api/v1/workflows" in paths
    assert "/api/v1/workflows/{workflow_id}" in paths
    assert "/api/v1/workflows/{workflow_id}/preferences" in paths
    assert "/api/v1/catalog/sync" in paths


@pytest.mark.asyncio
async def test_main_root_and_health(main_app: FastAPI):
    transport = httpx.ASGITransport(app=main_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        root_response = await client.get("/")
        assert root_response.status_code == 200
        assert root_response.json() == {
            "greeting": "Hello, World!",
            "message": "Welcome to FastAPI!",
        }

        health_response = await client.get("/healthz")
        assert health_response.status_code == 200
        assert health_response.json() == {"status": "ok"}
