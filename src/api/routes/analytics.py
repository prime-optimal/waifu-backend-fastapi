"""Analytics and metrics endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, field_serializer

from ...app.dependencies import get_analytics_service
from ...services.analytics import AnalyticsService

router = APIRouter(tags=["analytics"])


class ProcessingMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    retry_count: int

    @field_serializer("started_at", "completed_at")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class WorkflowMetricsResponse(BaseModel):
    workflow_id: uuid.UUID
    metrics: list[ProcessingMetricResponse]


class CostumePopularityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    attempt_count: int
    success_count: int
    average_processing_time: Optional[float] = None


class CostumeStatsResponse(BaseModel):
    costume_id: uuid.UUID
    stats: list[CostumePopularityResponse]


@router.get(
    "/analytics/workflow/{workflow_id}/metrics", response_model=WorkflowMetricsResponse
)
async def get_workflow_metrics(
    workflow_id: uuid.UUID,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> WorkflowMetricsResponse:
    """Get all processing metrics for a workflow run."""
    metrics = await analytics_service.get_workflow_metrics(workflow_id)
    return WorkflowMetricsResponse(
        workflow_id=workflow_id,
        metrics=[ProcessingMetricResponse.model_validate(m) for m in metrics],
    )


@router.get("/analytics/costume/{costume_id}", response_model=CostumeStatsResponse)
async def get_costume_popularity(
    costume_id: uuid.UUID,
    start_date: date,
    end_date: date,
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> CostumeStatsResponse:
    """Get popularity statistics for a costume within a date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )
    stats = await analytics_service.get_costume_stats(costume_id, start_date, end_date)
    return CostumeStatsResponse(
        costume_id=costume_id,
        stats=[CostumePopularityResponse.model_validate(s) for s in stats],
    )
