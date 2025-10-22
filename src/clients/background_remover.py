"""Client for background removal provider."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseServiceClient


@dataclass(slots=True)
class BackgroundRemovalResult:
    asset_url: str


class BackgroundRemoverClient(BaseServiceClient):
    async def remove_background(self, *, image_url: str) -> BackgroundRemovalResult:
        payload = {"image_url": image_url}
        data = await self._post_json("/remove", payload)
        return BackgroundRemovalResult(asset_url=data["asset_url"])
