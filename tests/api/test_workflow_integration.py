import asyncio
import uuid

import httpx
import pytest

from src.app.dependencies import get_catalog_service, get_database, get_workflow_service
from src.app.factory import create_app
from src.app.settings import AppSettings
from src.clients.background_remover import BackgroundRemovalResult
from src.clients.seedream import SeedreamResult
from src.clients.google_generation import GoogleGenerationResult
from src.db.repositories.costumes import CostumeRecord, CostumeRepository
from src.services.workflow import WorkflowService


class StubStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def upload_bytes(self, path: str, data: bytes, *, content_type: str) -> str:
        self.files[path] = data
        return f"https://cdn.test/file/catalog/{path}"

    async def upload_json(self, path: str, payload) -> str:
        import json

        self.files[path] = json.dumps(payload).encode()
        return f"https://cdn.test/file/catalog/{path}"

    async def close(self) -> None:
        return None


class StubBackgroundClient:
    async def remove_background(self, *, image_url: str) -> BackgroundRemovalResult:
        return BackgroundRemovalResult(asset_url=f"{image_url}-bg")

    async def close(self) -> None:
        return None


class StubSeedreamClient:
    async def generate(self, *, prompt: str, reference_url: str) -> SeedreamResult:
        return SeedreamResult(asset_url=f"{reference_url}-seedream", prompt=f"{prompt} v2")

    async def close(self) -> None:
        return None


class StubGoogleClient:
    async def generate(self, *, prompt: str, seedream_asset_url: str) -> GoogleGenerationResult:
        return GoogleGenerationResult(asset_url=f"{seedream_asset_url}-final", rationale="ok")

    async def close(self) -> None:
        return None


class StubCatalogService:
    def __init__(self) -> None:
        self.calls = 0

    async def manual_refresh(self) -> int:
        self.calls += 1
        return self.calls


@pytest.fixture
async def test_app(tmp_path):
    settings = AppSettings(
        app_name="Test App",
        database_url=f"sqlite+aiosqlite:///{tmp_path/'app.db'}",
        b2_key_id="key",
        b2_application_key="secret",
        b2_bucket_id="bucket",
        b2_download_url="https://cdn.test",
        b2_api_url="https://api.test",
        background_remover_url="https://bg.test",
        seedream_url="https://seedream.test",
        google_generation_url="https://google.test",
        feature_workflows_enabled=True,
    )

    app = create_app(settings=settings)

    database = app.dependency_overrides[get_database]()
    await database.create_all()

    repo = CostumeRepository()
    costume_id = uuid.uuid4()
    async with database.session() as session:
        await repo.upsert_costumes(
            session,
            [
                CostumeRecord(
                    id=costume_id,
                    name="Hero",
                    prompt="Hero prompt",
                    reference_image_url="https://ref.test/image.png",
                    affiliate_link=None,
                )
            ],
        )
        await session.commit()

    workflow_service = WorkflowService(
        settings=settings,
        database=database,
        storage=StubStorage(),
        background_client=StubBackgroundClient(),
        seedream_client=StubSeedreamClient(),
        google_client=StubGoogleClient(),
    )
    catalog_service = StubCatalogService()

    app.dependency_overrides[get_workflow_service] = lambda: workflow_service
    app.dependency_overrides[get_catalog_service] = lambda: catalog_service

    yield app, costume_id, workflow_service, catalog_service

    await workflow_service.close()


@pytest.mark.asyncio
async def test_full_workflow(test_app):
    app, costume_id, _, _ = test_app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        upload_response = await client.post(
            "/api/v1/uploads",
            files={"file": ("selfie.png", b"image-bytes", "image/png")},
        )
        assert upload_response.status_code == 201
        payload = upload_response.json()

        workflow_response = await client.post(
            "/api/v1/workflows",
            json={
                "session_id": payload["session_id"],
                "costume_id": str(costume_id),
                "uploaded_asset_url": payload["asset_url"],
            },
        )
        assert workflow_response.status_code == 202
        workflow_body = workflow_response.json()

        result_response = await client.get(f"/api/v1/workflows/{workflow_body['workflow_id']}")
        assert result_response.status_code == 200

        pref_response = await client.post(
            f"/api/v1/workflows/{workflow_body['workflow_id']}/preferences",
            json={"selection_url": workflow_body["final_asset_url"]},
        )
        assert pref_response.status_code == 200


@pytest.mark.asyncio
async def test_catalog_sync_endpoint(test_app):
    app, _, _, catalog_service = test_app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/catalog/sync")
        assert response.status_code == 202
        await asyncio.sleep(0)

    assert catalog_service.calls == 1
