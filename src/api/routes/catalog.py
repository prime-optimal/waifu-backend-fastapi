"""Catalog management endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel

from ...app.dependencies import get_catalog_service
from ...services.catalog import CatalogService

router = APIRouter(tags=["catalog"])


class CatalogSyncResponse(BaseModel):
    accepted: bool


@router.post("/catalog/sync", response_model=CatalogSyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_catalog_sync(
    background_tasks: BackgroundTasks,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> CatalogSyncResponse:
    background_tasks.add_task(catalog_service.manual_refresh)
    return CatalogSyncResponse(accepted=True)
