"""Client for AI provider multi-model try-on generation."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

from .base import BaseServiceClient


@dataclass(slots=True)
class AIProviderResult:
    model_name: str
    asset_url: str
    processing_time_ms: int
    status: str
    error_reason: str | None = None


class AIProviderClient(BaseServiceClient):
    def __init__(self, base_url: str, *, api_key: str | None = None, **kwargs) -> None:
        super().__init__(base_url, **kwargs)
        self._api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including API key if available."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Override to add API key headers."""
        response = await self.client.post(
            path, json=payload, headers=self._get_headers()
        )
        if response.status_code >= 400:
            raise Exception(
                f"Service responded with {response.status_code}: {response.text}"
            )
        return response.json()

    def _image_to_data_url(self, image_path: str) -> str:
        """Convert image file to base64 data URL."""
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            ext = image_path.lower().split(".")[-1]
            mime_type = "jpeg" if ext == "jpg" else ext
            return f"data:image/{mime_type};base64,{encoded_image}"

    async def generate_try_on(
        self,
        *,
        model_name: str,
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: list[str] | None = None,
        costume_reference_paths: list[str] | None = None,
        prompt: str,
        seed: int | None = None,
    ) -> AIProviderResult:
        """Generate try-on image using specified model with NanoGPT API format.

        Args:
            model_name: Name of the AI model to use
            user_image_url: URL of user uploaded image (optional)
            user_image_base64: Base64 encoded user image (optional)
            user_image_path: Local path to user image (optional)
            costume_reference_urls: List of URLs for costume reference images (optional)
            costume_reference_paths: List of local paths for costume reference images (optional)
            prompt: Text prompt for image generation
            seed: Seed for reproducible results (optional)

        Returns:
            AIProviderResult with generated image URL and metadata

        Raises:
            ServiceError: If the API call fails
            ValueError: If neither user_image_url, user_image_base64, nor user_image_path provided
        """
        start_time = time.time()

        # Validate user image input
        if not user_image_url and not user_image_base64 and not user_image_path:
            raise ValueError(
                "Either user_image_url, user_image_base64, or user_image_path must be provided"
            )

        # Build references array
        references = []

        # Add user image
        if user_image_url:
            references.append(
                {"id": "user", "kind": "url", "value": user_image_url, "role": "user"}
            )
        elif user_image_base64:
            references.append(
                {
                    "id": "user",
                    "kind": "base64",
                    "value": user_image_base64,
                    "role": "user",
                }
            )
        elif user_image_path:
            user_data_url = self._image_to_data_url(user_image_path)
            references.append(
                {"id": "user", "kind": "base64", "value": user_data_url, "role": "user"}
            )

        # Add costume reference images
        if costume_reference_urls:
            for i, url in enumerate(costume_reference_urls):
                references.append(
                    {
                        "id": f"costume-{i + 1}",
                        "kind": "url",
                        "value": url,
                        "role": "costume",
                    }
                )
        elif costume_reference_paths:
            for i, path in enumerate(costume_reference_paths):
                costume_data_url = self._image_to_data_url(path)
                references.append(
                    {
                        "id": f"costume-{i + 1}",
                        "kind": "base64",
                        "value": costume_data_url,
                        "role": "costume",
                    }
                )

        # Build NanoGPT API payload
        payload: dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "numOutputs": 1,
            "resolution": "auto",
            "steps": 30,
            "references": references,
        }

        if seed is not None:
            payload["options"] = {"seed": seed}

        try:
            data = await self._post_json("/", payload)  # NanoGPT uses root path

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract base64 image from response
            if data.get("data") and len(data["data"]) > 0:
                base64_data = data["data"][0].get("b64_json", "")
                if base64_data:
                    # For now, return base64 as "URL" - will be uploaded to B2 later
                    asset_url = f"data:image/png;base64,{base64_data}"
                    return AIProviderResult(
                        model_name=model_name,
                        asset_url=asset_url,
                        processing_time_ms=processing_time_ms,
                        status="success",
                        error_reason=None,
                    )

            return AIProviderResult(
                model_name=model_name,
                asset_url="",
                processing_time_ms=processing_time_ms,
                status="failed",
                error_reason="No image data in response",
            )

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            return AIProviderResult(
                model_name=model_name,
                asset_url="",
                processing_time_ms=processing_time_ms,
                status="failed",
                error_reason=str(e),
            )

    async def generate_try_on_parallel(
        self,
        *,
        model_names: list[str],
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: list[str] | None = None,
        costume_reference_paths: list[str] | None = None,
        prompt: str,
        seed: int | None = None,
        max_concurrent: int = 3,
    ) -> list[AIProviderResult]:
        """Generate try-on images using multiple models in parallel.

        Args:
            model_names: List of model names to use
            user_image_url: URL of user uploaded image (optional)
            user_image_base64: Base64 encoded user image (optional)
            user_image_path: Local path to user image (optional)
            costume_reference_urls: List of URLs for costume reference images (optional)
            costume_reference_paths: List of local paths for costume reference images (optional)
            prompt: Text prompt for image generation
            seed: Seed for reproducible results (optional)
            max_concurrent: Maximum number of concurrent requests

        Returns:
            List of AIProviderResult for each model
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single(model_name: str) -> AIProviderResult:
            async with semaphore:
                # Use different seeds for different models if seed is provided
                model_seed = (
                    seed + hash(model_name) % 1000 if seed is not None else None
                )
                return await self.generate_try_on(
                    model_name=model_name,
                    user_image_url=user_image_url,
                    user_image_base64=user_image_base64,
                    user_image_path=user_image_path,
                    costume_reference_urls=costume_reference_urls,
                    costume_reference_paths=costume_reference_paths,
                    prompt=prompt,
                    seed=model_seed,
                )

        tasks = [generate_single(model_name) for model_name in model_names]
        return await asyncio.gather(*tasks)
