import httpx
import pytest

from src.storage.b2 import B2Storage


@pytest.mark.asyncio
async def test_upload_bytes_success():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("b2_authorize_account"):
            return httpx.Response(
                200,
                json={
                    "apiUrl": "https://api.backblazeb2.com",
                    "authorizationToken": "auth-token",
                    "downloadUrl": "https://cdn.example.com",
                    "allowed": {"bucketName": "catalog"},
                },
            )
        if request.url.path.endswith("b2_get_upload_url"):
            assert request.headers["Authorization"] == "auth-token"
            return httpx.Response(
                200,
                json={
                    "uploadUrl": "https://upload.example.com/file",
                    "authorizationToken": "upload-token",
                },
            )
        if request.url.host == "upload.example.com":
            calls.append(request.content)
            assert request.headers["Authorization"] == "upload-token"
            return httpx.Response(200, json={"fileId": "123"})
        raise AssertionError(f"Unexpected request: {request.url}")

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    storage = B2Storage(
        key_id="key",
        application_key="secret",
        bucket_id="bucket-1",
        download_url="https://cdn.example.com",
        client=client,
    )

    url = await storage.upload_bytes("tmp/session/file.png", b"data", content_type="image/png")

    assert url == "https://cdn.example.com/file/catalog/tmp/session/file.png"
    assert calls == [b"data"]

    await storage.close()
