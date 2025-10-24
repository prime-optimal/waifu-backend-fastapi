"""Shared HTTP client utilities for external services."""

from __future__ import annotations

from typing import Any

import httpx


class ServiceError(RuntimeError):
    pass


class BaseServiceClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    @property
    def client(self) -> httpx.AsyncClient:
        return self._client

    async def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout: float | httpx.Timeout | None = None,
    ) -> dict[str, Any]:
        response = await self.client.post(path, json=payload, timeout=timeout)
        if response.status_code >= 400:
            raise ServiceError(
                f"Service responded with {response.status_code}: {response.text}"
            )
        return response.json()

    async def close(self) -> None:
        await self.client.aclose()
