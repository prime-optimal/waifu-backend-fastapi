import asyncio
import json
import os
import uuid
from pathlib import Path

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
        return SeedreamResult(
            asset_url=f"{reference_url}-seedream", prompt=f"{prompt} v2"
        )

    async def close(self) -> None:
        return None


class StubGoogleClient:
    async def generate(
        self, *, prompt: str, seedream_asset_url: str
    ) -> GoogleGenerationResult:
        return GoogleGenerationResult(
            asset_url=f"{seedream_asset_url}-final", rationale="ok"
        )

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
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'app.db'}",
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

        result_response = await client.get(
            f"/api/v1/workflows/{workflow_body['workflow_id']}"
        )
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


@pytest.mark.asyncio
@pytest.mark.external
async def test_real_ai_provider_all_user_images():
    """Test all 3 user images with all 3 models against real NanoGPT API."""
    import json
    from pathlib import Path
    from src.clients.ai_provider import AIProviderClient
    from src.clients.utils import image_to_data_url

    api_key = os.getenv("AI_PROVIDER_API_KEY")
    if not api_key:
        pytest.skip("AI_PROVIDER_API_KEY not set")

    api_url = os.getenv("AI_PROVIDER_URL", "https://nano-gpt.com/v1/images/generations")

    test_images_dir = Path(__file__).parent.parent / "fixtures" / "test_images"
    costumes_path = Path(__file__).parent.parent / "fixtures" / "test_costumes.json"

    with open(costumes_path) as f:
        fixtures = json.load(f)

    costume = fixtures["test_costumes"][0]
    user_images = ["user1.jpeg", "user2.jpeg", "user3.jpeg"]
    models = ["seedream-v4", "google:4@1", "gpt-image-1-mini"]

    costume_paths = [test_images_dir / img for img in costume["reference_images"]]

    client = AIProviderClient(api_url, api_key=api_key)

    results_summary = {
        "total_tests": 0,
        "successful": 0,
        "failed": 0,
        "by_user": {},
        "by_model": {m: {"success": 0, "failed": 0} for m in models},
    }

    try:
        for user_idx, user_image in enumerate(user_images, 1):
            user_image_path = test_images_dir / user_image
            if not user_image_path.exists():
                print(f"⚠️  Skipping {user_image} — file not found")
                continue

            print(f"\n📸 Testing user image {user_idx}/3: {user_image}")
            user_results = {"model_results": []}
            results_summary["by_user"][user_image] = user_results

            for model_name in models:
                print(f"  → Trying model: {model_name}")
                results_summary["total_tests"] += 1

                try:
                    result = await client.generate_try_on(
                        model_name=model_name,
                        user_image_path=str(user_image_path),
                        costume_reference_paths=[str(p) for p in costume_paths],
                        prompt=costume["prompt"],
                        seed=1000 + user_idx,
                    )

                    if result.status == "success":
                        print(
                            f"    ✅ Status: {result.status} | "
                            f"Time: {result.processing_time_ms}ms | "
                            f"File: {result.generated_filename}"
                        )
                        results_summary["successful"] += 1
                        results_summary["by_model"][model_name]["success"] += 1
                        user_results["model_results"].append(
                            {
                                "model": model_name,
                                "status": "success",
                                "processing_time_ms": result.processing_time_ms,
                                "filename": result.generated_filename,
                            }
                        )
                    else:
                        print(
                            f"    ❌ Status: {result.status} | "
                            f"Error: {result.error_reason}"
                        )
                        results_summary["failed"] += 1
                        results_summary["by_model"][model_name]["failed"] += 1
                        user_results["model_results"].append(
                            {
                                "model": model_name,
                                "status": "failed",
                                "error": result.error_reason,
                            }
                        )

                except Exception as e:
                    print(f"    ❌ Exception: {str(e)}")
                    results_summary["failed"] += 1
                    results_summary["by_model"][model_name]["failed"] += 1
                    user_results["model_results"].append(
                        {"model": model_name, "status": "exception", "error": str(e)}
                    )

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total generations attempted: {results_summary['total_tests']}")
        print(f"✅ Successful: {results_summary['successful']}")
        print(f"❌ Failed: {results_summary['failed']}")
        print("\nBy Model:")
        for model in models:
            stats = results_summary["by_model"][model]
            print(f"  {model}: {stats['success']} success, {stats['failed']} failed")

        assert results_summary["successful"] > 0, "At least one generation must succeed"

    finally:
        await client.close()
