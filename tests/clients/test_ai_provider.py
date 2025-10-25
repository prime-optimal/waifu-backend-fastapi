"""Tests for AI Provider client."""

from __future__ import annotations

import asyncio
import base64
import httpx
import json
import pytest
from pathlib import Path

from src.clients.ai_provider import AIProviderClient, AIProviderResult
from src.clients.utils import image_to_data_url


@pytest.fixture
def test_costumes():
    """Load test costume data."""
    costumes_path = Path(__file__).parent.parent / "fixtures" / "test_costumes.json"
    with open(costumes_path) as f:
        return json.load(f)


@pytest.fixture
def test_images_dir():
    """Get test images directory path."""
    return Path(__file__).parent.parent / "fixtures" / "test_images"


def _mock_nano_gpt_response(base64_data: str | None = None):
    """Create a mock NanoGPT API response."""
    if base64_data is None:
        # Generate a minimal test image
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

    return {"data": [{"b64_json": base64_data}]}


def _mock_transport_nano_gpt(
    response_payload: dict, expected_prompt: str | None = None
):
    """Create a mock transport for NanoGPT API."""

    async def handler(request: httpx.Request) -> httpx.Response:
        # Simulate some processing time
        await asyncio.sleep(0.01)  # 10ms delay

        # Verify request format
        assert request.url.path in ["/", "/v1/images/generations/"]
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("Bearer ")

        # Verify payload structure
        body = json.loads(request.content)
        assert "model" in body
        assert "prompt" in body
        assert "references" in body
        assert isinstance(body["references"], list)

        # Verify prompt content if provided
        if expected_prompt:
            assert body["prompt"] == expected_prompt, (
                f"Expected prompt: {expected_prompt[:100]}..., Got: {body['prompt'][:100]}..."
            )
        else:
            # At minimum, prompt should not be empty and should contain costume-related content
            assert len(body["prompt"]) > 50, "Prompt should be substantial"
            assert (
                "costume" in body["prompt"].lower()
                or "bowsette" in body["prompt"].lower()
            ), "Prompt should contain costume-related content"

        # Verify references structure
        user_refs = [r for r in body["references"] if r["role"] == "user"]
        costume_refs = [r for r in body["references"] if r["role"] == "costume"]

        assert len(user_refs) == 1, "Should have exactly one user reference"
        assert len(costume_refs) >= 1, "Should have at least one costume reference"

        return httpx.Response(200, json=response_payload)

    return httpx.MockTransport(handler)


def _mock_transport_error(
    status_code: int, text: str, expected_prompt: str | None = None
):
    """Create a mock transport that returns an error."""

    async def handler(request: httpx.Request) -> httpx.Response:
        # Simulate some processing time
        await asyncio.sleep(0.01)  # 10ms delay

        # Still validate the request format even for error cases
        if expected_prompt:
            body = json.loads(request.content)
            assert body["prompt"] == expected_prompt, (
                f"Expected prompt: {expected_prompt[:100]}..., Got: {body['prompt'][:100]}..."
            )

        return httpx.Response(status_code, text=text)

    return httpx.MockTransport(handler)


@pytest.fixture
def mock_client():
    """Create a mock AI provider client."""
    return AIProviderClient(
        base_url="https://nano-gpt.com/v1/images/generations", api_key="test-api-key"
    )


@pytest.mark.asyncio
async def test_generate_try_on_with_urls(mock_client, test_costumes, test_images_dir):
    """Test try-on generation with image URLs."""
    costume = test_costumes["test_costumes"][0]
    mock_response = _mock_nano_gpt_response()

    transport = _mock_transport_nano_gpt(
        mock_response, expected_prompt=costume["prompt"]
    )
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    costume_urls = [f"https://example.com/{img}" for img in costume["reference_images"]]

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=costume_urls,
        prompt=costume["prompt"],
        seed=1001,
    )

    assert isinstance(result, AIProviderResult)
    assert result.model_name == "seedream-v4"
    assert result.asset_url.startswith("data:image/png;base64,")
    assert result.status == "success"
    assert result.error_reason is None
    assert result.processing_time_ms > 0
    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_with_paths(mock_client, test_costumes, test_images_dir):
    """Test try-on generation with local image paths."""
    costume = test_costumes["test_costumes"][0]
    mock_response = _mock_nano_gpt_response()

    transport = _mock_transport_nano_gpt(
        mock_response, expected_prompt=costume["prompt"]
    )
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    user_image_path = test_images_dir / "user1.jpeg"
    costume_paths = [test_images_dir / img for img in costume["reference_images"]]

    result = await client.generate_try_on(
        model_name="google:4@1",
        user_image_path=str(user_image_path),
        costume_reference_paths=[str(p) for p in costume_paths],
        prompt=costume["prompt"],
        seed=1002,
    )

    assert result.model_name == "google:4@1"
    assert result.status == "success"
    assert result.asset_url.startswith("data:image/png;base64,")
    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_with_base64(mock_client, test_costumes):
    """Test try-on generation with base64 images."""
    costume = test_costumes["test_costumes"][0]
    mock_response = _mock_nano_gpt_response()

    transport = _mock_transport_nano_gpt(
        mock_response, expected_prompt=costume["prompt"]
    )
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    result = await client.generate_try_on(
        model_name="gpt-image-1-mini",
        user_image_base64="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
        costume_reference_urls=[
            "https://example.com/costume1.jpg",
            "https://example.com/costume2.jpg",
        ],
        prompt=costume["prompt"],
        seed=1003,
    )

    assert result.model_name == "gpt-image-1-mini"
    assert result.status == "success"
    assert result.asset_url.startswith("data:image/png;base64,")
    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_missing_image(mock_client, test_costumes):
    """Test error when no image input provided."""
    with pytest.raises(
        ValueError,
        match="Either user_image_url, user_image_base64, or user_image_path must be provided",
    ):
        await mock_client.generate_try_on(
            model_name="seedream-v4",
            costume_reference_urls=["https://example.com/costume.jpg"],
            prompt=test_costumes["test_costumes"][0]["prompt"],
        )


@pytest.mark.asyncio
async def test_generate_try_on_service_error(mock_client, test_costumes):
    """Test handling of service errors."""
    costume = test_costumes["test_costumes"][0]
    transport = _mock_transport_error(
        500, "Internal Server Error", expected_prompt=costume["prompt"]
    )
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=["https://example.com/costume.jpg"],
        prompt=test_costumes["test_costumes"][0]["prompt"],
    )

    assert result.status == "failed"
    assert "Internal Server Error" in result.error_reason
    assert result.processing_time_ms > 0
    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_invalid_response(mock_client, test_costumes):
    """Test handling of invalid API response."""
    costume = test_costumes["test_costumes"][0]
    transport = _mock_transport_nano_gpt(
        {"data": []}, expected_prompt=costume["prompt"]
    )  # Empty data array
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=["https://example.com/costume.jpg"],
        prompt=test_costumes["test_costumes"][0]["prompt"],
    )

    assert result.status == "failed"
    assert "No image data in response" in result.error_reason
    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_parallel_success(
    mock_client, test_costumes, test_images_dir
):
    """Test parallel generation with all models succeeding."""
    costume = test_costumes["test_costumes"][0]

    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        # Simulate processing time
        await asyncio.sleep(0.01)

        # Verify request format for each call
        assert request.url.path in ["/", "/v1/images/generations/"]
        body = json.loads(request.content)
        assert body["model"] in ["seedream-v4", "google:4@1", "gpt-image-1-mini"]

        # Validate prompt content
        assert "bowsette" in body["prompt"].lower(), (
            "Prompt should contain Bowsette content"
        )
        assert len(body["prompt"]) > 100, "Prompt should be substantial"

        call_count += 1
        return httpx.Response(200, json=_mock_nano_gpt_response())

    transport = httpx.MockTransport(handler)
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    results = await client.generate_try_on_parallel(
        model_names=["seedream-v4", "google:4@1", "gpt-image-1-mini"],
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=[
            "https://example.com/costume1.jpg",
            "https://example.com/costume2.jpg",
        ],
        prompt=costume["prompt"],
        seed=1001,
        max_concurrent=2,
    )

    assert len(results) == 3
    assert call_count == 3  # Should make 3 API calls

    model_names = [r.model_name for r in results]
    assert "seedream-v4" in model_names
    assert "google:4@1" in model_names
    assert "gpt-image-1-mini" in model_names

    for result in results:
        assert result.status == "success"
        assert result.asset_url.startswith("data:image/png;base64,")
        assert result.processing_time_ms > 0

    await client.close()


@pytest.mark.asyncio
async def test_generate_try_on_parallel_partial_failure(mock_client, test_costumes):
    """Test parallel generation with some models failing."""
    call_count = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        # Simulate processing time
        await asyncio.sleep(0.01)

        body = json.loads(request.content)

        # Validate prompt content
        assert "bowsette" in body["prompt"].lower(), (
            "Prompt should contain Bowsette content"
        )
        assert len(body["prompt"]) > 100, "Prompt should be substantial"

        call_count += 1
        if body["model"] == "seedream-v4":
            return httpx.Response(200, json=_mock_nano_gpt_response())
        else:
            return httpx.Response(500, text="Model overloaded")

    transport = httpx.MockTransport(handler)
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    results = await client.generate_try_on_parallel(
        model_names=["seedream-v4", "google:4@1"],
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=["https://example.com/costume.jpg"],
        prompt=test_costumes["test_costumes"][0]["prompt"],
        max_concurrent=2,
    )

    assert len(results) == 2

    # First model should succeed
    seedream_result = next(r for r in results if r.model_name == "seedream-v4")
    assert seedream_result.status == "success"

    # Second model should fail
    google_result = next(r for r in results if r.model_name == "google:4@1")
    assert google_result.status == "failed"
    assert "Model overloaded" in google_result.error_reason

    await client.close()


@pytest.mark.asyncio
async def test_image_to_data_url(test_images_dir):
    """Test image to data URL conversion."""
    # Test JPEG
    jpeg_path = test_images_dir / "user1.jpeg"
    data_url = image_to_data_url(str(jpeg_path))
    assert data_url.startswith("data:image/jpeg;base64,")

    # Test JPG (should be treated as jpeg)
    jpg_path = test_images_dir / "bowsette-crown.jpg"
    data_url = image_to_data_url(str(jpg_path))
    assert data_url.startswith("data:image/jpeg;base64,")

    # Verify base64 is valid
    header, encoded = data_url.split(",", 1)
    base64.b64decode(encoded)  # Should not raise exception


@pytest.mark.asyncio
async def test_model_limits(test_costumes, test_images_dir):
    """Test that models respect their image limits."""
    costume = test_costumes["test_costumes"][0]

    # Test seedream-v4 with 10 images (should work)
    mock_response = _mock_nano_gpt_response()
    transport = _mock_transport_nano_gpt(
        mock_response, expected_prompt=costume["prompt"]
    )
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    # Create 10 costume reference URLs (max for seedream-v4)
    costume_urls = [f"https://example.com/costume{i}.jpg" for i in range(10)]

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=costume_urls,
        prompt=costume["prompt"],
    )

    assert result.status == "success"
    await client.close()


@pytest.mark.asyncio
async def test_api_key_headers():
    """Test that API key is properly included in headers."""
    mock_response = _mock_nano_gpt_response()

    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.01)  # Simulate processing time
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-api-key-123"
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key="test-api-key-123",
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=["https://example.com/costume.jpg"],
        prompt="test prompt",
    )

    assert result.status == "success"
    await client.close()


@pytest.mark.asyncio
async def test_no_api_key_headers():
    """Test that requests work without API key."""
    mock_response = _mock_nano_gpt_response()

    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.01)  # Simulate processing time
        assert "Authorization" not in request.headers
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)
    client = AIProviderClient(
        "https://nano-gpt.com/v1/images/generations",
        api_key=None,  # No API key
        client=httpx.AsyncClient(
            transport=transport, base_url="https://nano-gpt.com/v1/images/generations"
        ),
    )

    result = await client.generate_try_on(
        model_name="seedream-v4",
        user_image_url="https://example.com/user.jpg",
        costume_reference_urls=["https://example.com/costume.jpg"],
        prompt="test prompt",
    )

    assert result.status == "success"
    await client.close()
