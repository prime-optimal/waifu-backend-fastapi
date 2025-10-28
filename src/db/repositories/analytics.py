"""Repository for workflow metrics and costume popularity analytics."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import CostumePopularity, ProcessingMetrics


class AnalyticsRepository:
    """Repository providing access to analytics-related models."""

    async def record_metric(
        self,
        session: AsyncSession,
        *,
        workflow_run_id: uuid.UUID,
        step: str,
        started_at: datetime,
        completed_at: datetime | None = None,
        duration_ms: int | None = None,
        success: bool,
        error_message: str | None = None,
        retry_count: int = 0,
    ) -> ProcessingMetrics:
        """Persist a new processing metric entry for a workflow step."""
        computed_duration = duration_ms
        if computed_duration is None and completed_at is not None:
            delta = completed_at - started_at
            computed_duration = int(delta.total_seconds() * 1000)
        metric = ProcessingMetrics(
            workflow_run_id=workflow_run_id,
            step=step,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=computed_duration,
            success=success,
            error_message=error_message,
            retry_count=retry_count,
        )
        session.add(metric)
        await session.flush()
        return metric

    async def get_workflow_metrics(
        self,
        session: AsyncSession,
        workflow_run_id: uuid.UUID,
    ) -> list[ProcessingMetrics]:
        """Return all metrics recorded for a specific workflow run."""
        result = await session.execute(
            select(ProcessingMetrics)
            .where(ProcessingMetrics.workflow_run_id == workflow_run_id)
            .order_by(ProcessingMetrics.started_at.asc())
        )
        return list(result.scalars().all())

    async def get_costume_stats(
        self,
        session: AsyncSession,
        *,
        costume_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[CostumePopularity]:
        """Retrieve costume popularity stats for the provided date range (inclusive)."""
        result = await session.execute(
            select(CostumePopularity)
            .where(CostumePopularity.costume_id == costume_id)
            .where(CostumePopularity.date >= start_date)
            .where(CostumePopularity.date <= end_date)
            .order_by(CostumePopularity.date.asc())
        )
        return list(result.scalars().all())

    async def update_daily_stats(
        self,
        session: AsyncSession,
        *,
        costume_id: uuid.UUID,
        stats_date: date,
        attempt_increment: int = 0,
        success_increment: int = 0,
        processing_time_ms: int | None = None,
    ) -> CostumePopularity:
        """Increment or create daily popularity stats for a costume."""
        result = await session.execute(
            select(CostumePopularity)
            .where(CostumePopularity.costume_id == costume_id)
            .where(CostumePopularity.date == stats_date)
        )
        record = result.scalar_one_or_none()
        if record is None:
            attempt_count = max(attempt_increment, 0)
            success_count = max(success_increment, 0)
            average = (
                float(processing_time_ms)
                if processing_time_ms is not None
                else None
            )
            record = CostumePopularity(
                costume_id=costume_id,
                date=stats_date,
                attempt_count=attempt_count,
                success_count=success_count,
                average_processing_time=average,
            )
            session.add(record)
            await session.flush()
            return record

        existing_attempts = record.attempt_count or 0
        existing_success = record.success_count or 0
        existing_average = record.average_processing_time or 0.0

        new_attempts = max(existing_attempts + attempt_increment, 0)
        new_success = max(existing_success + success_increment, 0)

        record.attempt_count = new_attempts
        record.success_count = new_success

        if processing_time_ms is not None:
            weight = attempt_increment if attempt_increment > 0 else 1
            base_weight = existing_attempts if existing_attempts > 0 else 0
            total_weight = max(base_weight + weight, 1)
            weighted_sum = (
                existing_average * base_weight
                + float(processing_time_ms) * weight
            )
            record.average_processing_time = weighted_sum / total_weight

        await session.flush()
        return record

    async def get_avg_processing_time(
        self,
        session: AsyncSession,
        *,
        step: str,
        workflow_run_id: uuid.UUID | None = None,
    ) -> float | None:
        """Calculate the average processing duration (milliseconds) for a given step."""
        stmt = select(func.avg(ProcessingMetrics.duration_ms)).where(
            ProcessingMetrics.step == step
        )
        if workflow_run_id is not None:
            stmt = stmt.where(ProcessingMetrics.workflow_run_id == workflow_run_id)
        result = await session.execute(stmt)
        average = result.scalar()
        return float(average) if average is not None else None
