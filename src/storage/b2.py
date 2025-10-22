"""Backblaze B2 storage abstraction."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
from dataclasses import dataclass

import httpx


@dataclass(slots=True)
class B2AuthContext:
    api_url: str
    authorization_token: str
    download_url: str
    bucket_id: str
    bucket_name: str
    expires_at: float


class B2Storage:
    def __init__(
        self,
        *,
        key_id: str,
        application_key: str,
        bucket_id: str,
        download_url: str,
        api_url: str = "https://api.backblazeb2.com",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._key_id = key_id
        self._application_key = application_key
        self._bucket_id = bucket_id
        self._download_url = download_url
        self._api_url = api_url
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._auth: B2AuthContext | None = None

    async def upload_bytes(self, path: str, data: bytes, *, content_type: str) -> str:
        auth = await self._authorize()
        upload_info = await self._get_upload_url(auth)

        sha1_hash = hashlib.sha1(data).hexdigest()
        encoded_name = urllib.parse.quote(path)

        headers = {
            "Authorization": upload_info["authorizationToken"],
            "X-Bz-File-Name": encoded_name,
            "Content-Type": content_type,
            "X-Bz-Content-Sha1": sha1_hash,
        }

        response = await self._client.post(upload_info["uploadUrl"], headers=headers, content=data)
        response.raise_for_status()
        return f"{auth.download_url}/file/{upload_info['bucketName']}/{encoded_name}"

    async def upload_json(self, path: str, payload: dict | list) -> str:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return await self.upload_bytes(path, data, content_type="application/json")

    async def _authorize(self) -> B2AuthContext:
        if self._auth and self._auth.expires_at > time.time():
            return self._auth

        response = await self._client.get(
            f"{self._api_url}/b2api/v2/b2_authorize_account",
            auth=(self._key_id, self._application_key),
        )
        response.raise_for_status()
        data = response.json()
        self._auth = B2AuthContext(
            api_url=data["apiUrl"],
            authorization_token=data["authorizationToken"],
            download_url=data.get("downloadUrl", self._download_url),
            bucket_id=self._bucket_id,
            bucket_name=data["allowed"]["bucketName"],
            expires_at=time.time() + 23 * 60 * 60,
        )
        return self._auth

    async def _get_upload_url(self, auth: B2AuthContext) -> dict:
        headers = {"Authorization": auth.authorization_token}
        response = await self._client.post(
            f"{auth.api_url}/b2api/v2/b2_get_upload_url",
            headers=headers,
            json={"bucketId": auth.bucket_id},
        )
        response.raise_for_status()
        data = response.json()
        data["bucketName"] = auth.bucket_name
        return data

    async def close(self) -> None:
        await self._client.aclose()
