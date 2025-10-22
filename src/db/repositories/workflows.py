"""Repository for workflow run tracking and user preferences."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import WorkflowPreference, WorkflowRun, WorkflowStatus


@dataclass(slots=True)
class WorkflowRecord:
    workflow_id: uuid.UUID
    final_asset_url: str
    log_url: str


class WorkflowRepository:
    async def create_run(
        self,
        session: AsyncSession,
        *,
        user_session: uuid.UUID,
        costume_id: uuid.UUID,
        uploaded_asset_url: str,
    ) -> WorkflowRun:
        run = WorkflowRun(
            user_session=user_session,
            costume_id=costume_id,
            uploaded_asset_url=uploaded_asset_url,
        )
        session.add(run)
        await session.flush()
        return run

    async def mark_completed(
        self,
        session: AsyncSession,
        workflow_id: uuid.UUID,
        *,
        background_asset_url: str,
        seedream_asset_url: str,
        final_asset_url: str,
        log_object_path: str,
        detail: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        run = await session.get(WorkflowRun, workflow_id)
        if run is None:
            raise ValueError("Workflow not found")
        run.status = WorkflowStatus.completed
        run.background_asset_url = background_asset_url
        run.seedream_asset_url = seedream_asset_url
        run.final_asset_url = final_asset_url
        run.log_object_path = log_object_path
        run.detail = detail or {}
        return run

    async def mark_failed(
        self,
        session: AsyncSession,
        workflow_id: uuid.UUID,
        detail: dict[str, Any] | None = None,
    ) -> WorkflowRun | None:
        run = await session.get(WorkflowRun, workflow_id)
        if run is None:
            return None
        run.status = WorkflowStatus.failed
        run.detail = detail or {}
        return run

    async def get(self, session: AsyncSession, workflow_id: uuid.UUID) -> WorkflowRun | None:
        return await session.get(WorkflowRun, workflow_id)

    async def list_recent(self, session: AsyncSession, limit: int = 20) -> list[WorkflowRun]:
        result = await session.execute(
            select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def record_preference(
        self, session: AsyncSession, workflow_id: uuid.UUID, selection_url: str
    ) -> WorkflowPreference:
        preference = WorkflowPreference(workflow_id=workflow_id, selection_url=selection_url)
        session.add(preference)
        await session.flush()
        return preference
