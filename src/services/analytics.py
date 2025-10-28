"""Analytics and metrics service."""

from __future__ import annotations

import uuid
from datetime import date

from ..db.database import Database
from ..db.models import CostumePopularity, ProcessingMetrics
from ..db.repositories import AnalyticsRepository


class AnalyticsService:
    """Service for managing analytics and metrics data."""

    def __init__(
        self,
        database: Database,
        repository: AnalyticsRepository | None = None,
    ) -> None:
        self._database = database
        self._repository = repository or AnalyticsRepository()

    async def get_workflow_metrics(
        self, workflow_run_id: uuid.UUID
    ) -> list[ProcessingMetrics]:
        """Get all metrics for a workflow run."""
        async with self._database.session() as session:
            return await self._repository.get_workflow_metrics(session, workflow_run_id)

    async def get_costume_stats(
        self,
        costume_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[CostumePopularity]:
        """Get popularity stats for a costume within a date range."""
        async with self._database.session() as session:
            return await self._repository.get_costume_stats(
                session,
                costume_id=costume_id,
                start_date=start_date,
                end_date=end_date,
            )

    async def get_avg_processing_time(
        self,
        step: str,
        workflow_run_id: uuid.UUID | None = None,
    ) -> float | None:
        """Get average processing time for a step."""
        async with self._database.session() as session:
            return await self._repository.get_avg_processing_time(
                session,
                step=step,
                workflow_run_id=workflow_run_id,
            )
