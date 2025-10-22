"""Workflow orchestration service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, UploadFile, status

from ..app.settings import AppSettings
from ..clients import BackgroundRemoverClient, GoogleGenerationClient, SeedreamClient
from ..clients.background_remover import BackgroundRemovalResult
from ..clients.seedream import SeedreamResult
from ..db.database import Database
from ..db.repositories import CostumeRepository, WorkflowRepository
from ..storage import B2Storage


@dataclass(slots=True)
class WorkflowState:
    workflow_id: uuid.UUID
    final_asset_url: str
    log_url: str


class WorkflowService:
    def __init__(
        self,
        *,
        settings: AppSettings,
        database: Database,
        storage: B2Storage,
        background_client: BackgroundRemoverClient,
        seedream_client: SeedreamClient,
        google_client: GoogleGenerationClient,
        costume_repository: CostumeRepository | None = None,
        workflow_repository: WorkflowRepository | None = None,
    ) -> None:
        self._settings = settings
        self._database = database
        self._storage = storage
        self._background_client = background_client
        self._seedream_client = seedream_client
        self._google_client = google_client
        self._costume_repository = costume_repository or CostumeRepository()
        self._workflow_repository = workflow_repository or WorkflowRepository()

    @classmethod
    def from_settings(cls, settings: AppSettings, database: Database) -> "WorkflowService":
        storage = B2Storage(
            key_id=settings.b2_key_id,
            application_key=settings.b2_application_key,
            bucket_id=settings.b2_bucket_id,
            download_url=str(settings.b2_download_url),
            api_url=str(settings.b2_api_url),
        )
        background_client = BackgroundRemoverClient(str(settings.background_remover_url))
        seedream_client = SeedreamClient(str(settings.seedream_url))
        google_client = GoogleGenerationClient(str(settings.google_generation_url))
        return cls(
            settings=settings,
            database=database,
            storage=storage,
            background_client=background_client,
            seedream_client=seedream_client,
            google_client=google_client,
        )

    async def close(self) -> None:
        await self._storage.close()
        await self._background_client.close()
        await self._seedream_client.close()
        await self._google_client.close()

    async def store_upload(self, session_id: uuid.UUID, file: UploadFile) -> str:
        data = await file.read()
        path = f"{self._settings.workflow_tmp_prefix}/{session_id}/{file.filename or 'upload.bin'}"
        return await self._storage.upload_bytes(
            path,
            data,
            content_type=file.content_type or "application/octet-stream",
        )

    async def start_workflow(self, database: Database | None, payload) -> WorkflowState:
        db = database or self._database
        async with db.session() as session:
            costume = await self._costume_repository.get(session, payload.costume_id)
            if costume is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Costume not found")

            run = await self._workflow_repository.create_run(
                session,
                user_session=payload.session_id,
                costume_id=payload.costume_id,
                uploaded_asset_url=payload.uploaded_asset_url,
            )

            try:
                background = await self._background_client.remove_background(
                    image_url=payload.uploaded_asset_url
                )
                seedream_result = await self._seedream_client.generate(
                    prompt=costume.prompt, reference_url=background.asset_url
                )
                google_result = await self._google_client.generate(
                    prompt=seedream_result.prompt,
                    seedream_asset_url=seedream_result.asset_url,
                )
                log_payload = self._build_log_payload(
                    run.id,
                    payload.uploaded_asset_url,
                    background,
                    seedream_result,
                    google_result,
                )
                log_path = self._log_path(run.id)
                log_url = await self._storage.upload_json(log_path, log_payload)

                await self._workflow_repository.mark_completed(
                    session,
                    run.id,
                    background_asset_url=background.asset_url,
                    seedream_asset_url=seedream_result.asset_url,
                    final_asset_url=google_result.asset_url,
                    log_object_path=log_path,
                    detail={"log_url": log_url},
                )
                await session.commit()
                return WorkflowState(
                    workflow_id=run.id,
                    final_asset_url=google_result.asset_url,
                    log_url=log_url,
                )
            except Exception as exc:  # pragma: no cover - defensive
                await self._workflow_repository.mark_failed(
                    session,
                    run.id,
                    detail={"error": str(exc)},
                )
                await session.commit()
                raise

    async def get_workflow(self, database: Database | None, workflow_id: uuid.UUID) -> WorkflowState | None:
        db = database or self._database
        async with db.session() as session:
            record = await self._workflow_repository.get(session, workflow_id)
            if record is None or record.final_asset_url is None or record.log_object_path is None:
                return None
            details = record.detail or {}
            log_url = details.get("log_url")
            if log_url is None:
                log_url = f"{self._settings.b2_download_url}/file/{record.log_object_path}"
            return WorkflowState(
                workflow_id=record.id,
                final_asset_url=record.final_asset_url,
                log_url=log_url,
            )

    async def record_preference(
        self, database: Database | None, workflow_id: uuid.UUID, selection_url: str
    ) -> None:
        db = database or self._database
        async with db.session() as session:
            await self._workflow_repository.record_preference(
                session, workflow_id, selection_url
            )
            await session.commit()

    def _log_path(self, workflow_id: uuid.UUID) -> str:
        return f"{self._settings.workflow_log_prefix}/{workflow_id}.json"

    @staticmethod
    def _build_log_payload(
        workflow_id: uuid.UUID,
        uploaded_asset_url: str,
        background: BackgroundRemovalResult,
        seedream_result: SeedreamResult,
        google_result,
    ) -> dict[str, Any]:
        return {
            "workflow_id": str(workflow_id),
            "uploaded_asset_url": uploaded_asset_url,
            "background_asset_url": background.asset_url,
            "seedream_asset_url": seedream_result.asset_url,
            "google_asset_url": google_result.asset_url,
        }
