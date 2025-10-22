import httpx
import pytest

from src.clients.background_remover import BackgroundRemoverClient
from src.clients.google_generation import GoogleGenerationClient
from src.clients.seedream import SeedreamClient


def _mock_transport(expected_path: str, response_payload: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == expected_path
        return httpx.Response(200, json=response_payload)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_background_remover_client_posts_payload():
    transport = _mock_transport("/remove", {"asset_url": "https://example.com/bg.png"})
    client = BackgroundRemoverClient(
        "https://service.test",
        client=httpx.AsyncClient(transport=transport, base_url="https://service.test"),
    )

    result = await client.remove_background(image_url="https://example.com/source.png")

    assert result.asset_url == "https://example.com/bg.png"
    await client.close()


@pytest.mark.asyncio
async def test_seedream_client_generate():
    transport = _mock_transport(
        "/generate",
        {"asset_url": "https://example.com/seedream.png", "prompt": "refined prompt"},
    )
    client = SeedreamClient(
        "https://seedream.test",
        client=httpx.AsyncClient(transport=transport, base_url="https://seedream.test"),
    )

    result = await client.generate(prompt="base", reference_url="https://example.com/bg.png")

    assert result.asset_url == "https://example.com/seedream.png"
    assert result.prompt == "refined prompt"
    await client.close()


@pytest.mark.asyncio
async def test_google_generation_client_generate():
    transport = _mock_transport(
        "/generate",
        {"asset_url": "https://example.com/final.png", "rationale": "looks nice"},
    )
    client = GoogleGenerationClient(
        "https://google.test",
        client=httpx.AsyncClient(transport=transport, base_url="https://google.test"),
    )

    result = await client.generate(
        prompt="prompt",
        seedream_asset_url="https://example.com/seedream.png",
    )

    assert result.asset_url == "https://example.com/final.png"
    assert result.rationale == "looks nice"
    await client.close()
