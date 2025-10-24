"""Client for AI provider multi-model try-on generation."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import httpx

from .base import BaseServiceClient, ServiceError
from .utils import (
    generate_ai_filename,
    image_to_data_url,
    sanitize_model_name,
)

logger = logging.getLogger("waifu.ai_provider")

DEBUG_DIR = Path(os.getenv("AI_DEBUG_DIR", tempfile.gettempdir()))
DEBUG_ENABLED = os.getenv("AI_PROVIDER_DEBUG") == "1"
MAX_BYTES = 10 * 1024 * 1024  # 10MB limit for image downloads
CONNECT_TIMEOUT = 10.0
WRITE_TIMEOUT = 10.0

# Model-specific timeouts for image downloads
IMAGE_DOWNLOAD_TIMEOUTS = {
    "qwen-image": 180.0,  # 3 minutes for qwen-image (very slow)
    "seedream-v4": 45.0,  # 45 seconds for seedream-v4
    "google:4@1": 45.0,  # 45 seconds for google:4@1
}
DEFAULT_IMAGE_DOWNLOAD_TIMEOUT = 45.0  # Default fallback

# Model-specific timeouts for generation calls (read portion)
MODEL_GENERATION_TIMEOUTS = {
    "qwen-image": 180.0,
    "seedream-v4": 90.0,
    "google:4@1": 90.0,
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
        """Generate try-on image using specified model with NanoGPT API format."""
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

        references = list(
            self._build_references(
                model_name=model_name,
                user_image_url=user_image_url,
                user_image_base64=user_image_base64,
                user_image_path=user_image_path,
                costume_reference_urls=costume_reference_urls,
                costume_reference_paths=costume_reference_paths,
            )
        )

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
            model_name,
            DEFAULT_GENERATION_TIMEOUT,
        )
        generation_timeout = httpx.Timeout(
            connect=CONNECT_TIMEOUT,
            read=generation_read_timeout,
            write=WRITE_TIMEOUT,
        )

        try:
            data = await self._post_json(
                "",
                payload,
                timeout=generation_timeout,
            )
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)

            asset_url = ""
            generated_filename = None
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
                "Generated try-on",
                extra={
                    "model_name": model_name,
                    "status": status,
                    "processing_time_ms": processing_time_ms,
                    "payload_size_kb": round(payload_size_kb, 2),
                },
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

        except ServiceError:
            raise
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
                "AI provider generation failed",
                extra={"model_name": model_name},
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

        return await asyncio.gather(*(generate_single(m) for m in model_names))

    def _build_references(
        self,
        *,
        model_name: str,
        user_image_url: str | None = None,
        user_image_base64: str | None = None,
        user_image_path: str | None = None,
        costume_reference_urls: Sequence[str] | None = None,
        costume_reference_paths: Sequence[str] | None = None,
    ) -> Iterable[dict[str, Any]]:
        if user_image_url:
            yield {
                "id": "user",
                "kind": "url",
                "value": user_image_url,
                "role": "user",
            }
        elif user_image_base64:
            yield {
                "id": "user",
                "kind": "base64",
                "value": user_image_base64,
                "role": "user",
            }
        elif user_image_path:
            yield {
                "id": "user",
                "kind": "base64",
                "value": image_to_data_url(user_image_path),
                "role": "user",
            }

        def make_costume_ref(idx: int, kind: str, value: str) -> dict[str, Any]:
            return {
                "id": f"costume-{idx}",
                "kind": kind,
                "value": value,
                "role": "costume",
            }

        if costume_reference_urls:
            for idx, url in enumerate(costume_reference_urls, start=1):
                value = (
                    awaitable_to_base64(url, model_name=model_name)
                    if model_name == "qwen-image"
                    else url
                )
                kind = "base64" if model_name == "qwen-image" else "url"
                yield make_costume_ref(idx, kind, value)

        if costume_reference_paths:
            for idx, path in enumerate(costume_reference_paths, start=1):
                yield make_costume_ref(idx, "base64", image_to_data_url(path))

    @staticmethod
    def _describe_image_input(
        *,
        url: str | None,
        base64: str | None,
        path: str | None,
    ) -> dict[str, Any]:
        return {
            "url": bool(url),
            "base64_provided": bool(base64),
            "path_provided": bool(path),
            "base64_length": len(base64) if base64 else None,
            "path": path,
        }

    @staticmethod
    def _describe_costume_inputs(
        *,
        urls: Sequence[str] | None,
        paths: Sequence[str] | None,
    ) -> dict[str, Any]:
        return {
            "urls": len(urls or ()),
            "paths": len(paths or ()),
        }

    def _emit_debug(self, debug_info: dict[str, Any]) -> None:
        if not DEBUG_ENABLED:
            return

        debug_dir = DEBUG_DIR
        debug_dir.mkdir(parents=True, exist_ok=True)
        sanitized_model = sanitize_model_name(debug_info.get("model_name", "unknown"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = debug_dir / f"debug_{sanitized_model}_{timestamp}.json"

        try:
            import json

            with debug_filename.open("w", encoding="utf-8") as fh:
                json.dump(debug_info, fh, indent=2, default=str)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to write debug file", extra={"path": str(debug_filename)})


async def awaitable_to_base64(url: str, *, model_name: str) -> str:
    timeout_seconds = IMAGE_DOWNLOAD_TIMEOUTS.get(
        model_name,
        DEFAULT_IMAGE_DOWNLOAD_TIMEOUT,
    )
    request_timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=timeout_seconds,
        write=WRITE_TIMEOUT,
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=request_timeout)

    response.raise_for_status()
    if len(response.content) > MAX_BYTES:
        raise ServiceError(
            f"Image at {url} exceeds size limit ({len(response.content)} bytes)"
        )

    mime_type = response.headers.get("content-type", "image/png")
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"
