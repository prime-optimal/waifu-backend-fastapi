"""Client for Google generative model."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseServiceClient


@dataclass(slots=True)
class GoogleGenerationResult:
    asset_url: str
    rationale: str | None = None


class GoogleGenerationClient(BaseServiceClient):
    async def generate(
        self,
        *,
        prompt: str,
        seedream_asset_url: str,
    ) -> GoogleGenerationResult:
        payload = {"prompt": prompt, "seedream_asset_url": seedream_asset_url}
        data = await self._post_json("/generate", payload)
        return GoogleGenerationResult(
            asset_url=data["asset_url"], rationale=data.get("rationale")
        )
