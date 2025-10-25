"""Client for AI provider multi-model try-on generation."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Sequence

import httpx

from src.observability.logger import get_logger

from .base import BaseServiceClient, ServiceError
from .utils import generate_ai_filename, image_to_data_url

logger = get_logger("ai_provider")

DEBUG_DIR = Path(os.getenv("AI_DEBUG_DIR", tempfile.gettempdir()))
DEBUG_ENABLED = os.getenv("AI_PROVIDER_DEBUG") == "1"
MAX_BYTES = 10 * 1024 * 1024  # 10MB limit for image downloads
CONNECT_TIMEOUT = 10.0
WRITE_TIMEOUT = 10.0

IMAGE_DOWNLOAD_TIMEOUTS = {
    "qwen-image": 180.0,
    "seedream-v4": 45.0,
    "google:4@1": 45.0,
    "gpt-image-1-mini": 60.0,
}
DEFAULT_IMAGE_DOWNLOAD_TIMEOUT = 45.0

MODEL_GENERATION_TIMEOUTS = {
    "qwen-image": 180.0,
    "seedream-v4": 90.0,
    "google:4@1": 90.0,
    "gpt-image-1-mini": 90.0,
}
DEFAULT_GENERATION_TIMEOUT = 120.0


@dataclass(slots=True)
class AIProviderResult:
    model_name: str
    asset_url: str
    processing_time_ms: int
    status: str
    error_reason: str | None = None
    generated_filename: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProviderClient(BaseServiceClient):
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(base_url, timeout=timeout, client=client)
        self._api_key = api_key

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout: float | httpx.Timeout | None = None,
    ) -> dict[str, Any]:
        response = await self.client.post(
            path,
            json=payload,
            headers=self._get_headers(),
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise ServiceError(
                f"Service responded with {response.status_code}: {response.text}"
            )
        return response.json()

    async def generate_try_on(
        self,
        *,
        model_name: str,
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: Sequence[str] | None = None,
        costume_reference_paths: Sequence[str] | None = None,
        prompt: str,
        seed: int | None = None,
    ) -> AIProviderResult:
        start_time = time.perf_counter()

        if not any([user_image_url, user_image_base64, user_image_path]):
            raise ValueError(
                "Either user_image_url, user_image_base64, or user_image_path must be provided"
            )

        debug_info: dict[str, Any] = {
            "model_name": model_name,
            "prompt_length": len(prompt),
            "seed": seed,
            "user_image_input": self._describe_image_input(
                url=user_image_url,
                base64=user_image_base64,
                path=user_image_path,
            ),
            "costume_reference_counts": self._describe_costume_inputs(
                urls=costume_reference_urls,
                paths=costume_reference_paths,
            ),
        }

        references = [
            ref
            async for ref in self._build_references(
                model_name=model_name,
                user_image_url=user_image_url,
                user_image_base64=user_image_base64,
                user_image_path=user_image_path,
                costume_reference_urls=costume_reference_urls,
                costume_reference_paths=costume_reference_paths,
            )
        ]

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

        payload_size_kb = len(str(payload)) / 1024
        debug_info["payload_size_kb"] = round(payload_size_kb, 2)

        generation_read_timeout = MODEL_GENERATION_TIMEOUTS.get(
            model_name, DEFAULT_GENERATION_TIMEOUT
        )
        generation_timeout = httpx.Timeout(
            connect=CONNECT_TIMEOUT,
            read=generation_read_timeout,
            write=WRITE_TIMEOUT,
            pool=5.0,
        )

        try:
            data = await self._post_json("", payload, timeout=generation_timeout)
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            asset_url = ""
            generated_filename: str | None = None
            metadata: dict[str, Any] = {}

            if isinstance(data, dict):
                debug_info["raw_response_keys"] = list(data.keys())
                if data.get("data"):
                    entry = data["data"][0]
                    base64_data = entry.get("b64_json")
                    if base64_data:
                        generated_filename = generate_ai_filename(model_name=model_name)
                        asset_url = f"data:image/png;base64,{base64_data}"
                        metadata["image_base64_length"] = len(base64_data)

            status = "success" if asset_url else "failed"
            error_reason = None if asset_url else "No image data in response"

            debug_info.update(
                {
                    "result_status": status,
                    "processing_time_ms": processing_time_ms,
                    "generated_filename": generated_filename,
                }
            )
            self._emit_debug(debug_info)

            logger.info(
                "generated_try_on",
                model=model_name,
                status=status,
                processing_time_ms=processing_time_ms,
                payload_size_kb=round(payload_size_kb, 2),
                generated_filename=generated_filename,
            )

            return AIProviderResult(
                model_name=model_name,
                asset_url=asset_url,
                processing_time_ms=processing_time_ms,
                status=status,
                error_reason=error_reason,
                generated_filename=generated_filename,
                metadata=metadata,
            )
        except ServiceError as exc:
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            debug_info.update(
                {
                    "result_status": "failed",
                    "processing_time_ms": processing_time_ms,
                    "error": str(exc),
                }
            )
            self._emit_debug(debug_info)
            logger.error(
                "ai_provider_service_error",
                model=model_name,
                error=str(exc),
                processing_time_ms=processing_time_ms,
            )
            return AIProviderResult(
                model_name=model_name,
                asset_url="",
                processing_time_ms=processing_time_ms,
                status="failed",
                error_reason=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            debug_info.update(
                {
                    "result_status": "failed",
                    "processing_time_ms": processing_time_ms,
                    "error": str(exc),
                }
            )
            self._emit_debug(debug_info)
            logger.exception(
                "ai_provider_generation_failed",
                model=model_name,
                processing_time_ms=processing_time_ms,
            )
            return AIProviderResult(
                model_name=model_name,
                asset_url="",
                processing_time_ms=processing_time_ms,
                status="failed",
                error_reason=str(exc),
            )

    async def generate_try_on_parallel(
        self,
        *,
        model_names: Sequence[str],
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: Sequence[str] | None = None,
        costume_reference_paths: Sequence[str] | None = None,
        prompt: str,
        seed: int | None = None,
        max_concurrent: int = 3,
    ) -> list[AIProviderResult]:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single(model: str) -> AIProviderResult:
            async with semaphore:
                model_seed = seed + (hash(model) % 1000) if seed is not None else None
                return await self.generate_try_on(
                    model_name=model,
                    user_image_url=user_image_url,
                    user_image_base64=user_image_base64,
                    user_image_path=user_image_path,
                    costume_reference_urls=costume_reference_urls,
                    costume_reference_paths=costume_reference_paths,
                    prompt=prompt,
                    seed=model_seed,
                )

        return await asyncio.gather(*(generate_single(name) for name in model_names))

    def _describe_image_input(
        self,
        *,
        url: str | None = None,
        base64: str | None = None,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Describe the user image input for debugging."""
        if url:
            return {"type": "url", "value": url}
        if base64:
            preview = f"{base64[:50]}..." if len(base64) > 50 else base64
            return {"type": "base64", "value": preview}
        if path:
            return {"type": "path", "value": path}
        return {"type": "none", "value": None}

    def _describe_costume_inputs(
        self,
        *,
        urls: Sequence[str] | None = None,
        paths: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Describe costume reference inputs for debugging."""
        url_count = len(urls) if urls else 0
        path_count = len(paths) if paths else 0
        return {
            "url_count": url_count,
            "path_count": path_count,
            "total_count": url_count + path_count,
        }

    async def _build_references(
        self,
        *,
        model_name: str,
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: Sequence[str] | None = None,
        costume_reference_paths: Sequence[str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Build references array for the AI provider API."""
        if user_image_url:
            yield {"role": "user", "url": user_image_url}
        elif user_image_base64:
            yield {"role": "user", "base64": user_image_base64}
        elif user_image_path:
            data_url = image_to_data_url(user_image_path)
            yield {"role": "user", "base64": data_url.split(",", 1)[1]}

        if costume_reference_urls:
            for url in costume_reference_urls:
                yield {"role": "costume", "url": url}

        if costume_reference_paths:
            for path in costume_reference_paths:
                data_url = image_to_data_url(path)
                yield {"role": "costume", "base64": data_url.split(",", 1)[1]}

    def _emit_debug(self, debug_info: dict[str, Any]) -> None:
        """Emit debug information if debugging is enabled."""
        if not DEBUG_ENABLED:
            return

        debug_file = (
            DEBUG_DIR
            / f"ai_provider_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        with open(debug_file, "w") as f:
            json.dump(debug_info, f, indent=2, default=str)
        logger.debug("ai_provider_debug_written", debug_file=str(debug_file))
