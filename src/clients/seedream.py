"""Client for seedream model generation."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseServiceClient


@dataclass(slots=True)
class SeedreamResult:
    asset_url: str
    prompt: str


class SeedreamClient(BaseServiceClient):
    async def generate(self, *, prompt: str, reference_url: str) -> SeedreamResult:
        payload = {"prompt": prompt, "reference_url": reference_url}
        data = await self._post_json("/generate", payload)
        return SeedreamResult(asset_url=data["asset_url"], prompt=data.get("prompt", prompt))
