"""Workflow orchestration endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from ...app.dependencies import get_app_settings, get_database, get_workflow_service
from ...app.settings import AppSettings
from ...db.database import Database
from ...services.workflow import WorkflowService

router = APIRouter(tags=["workflows"])


class UploadResponse(BaseModel):
    session_id: uuid.UUID
    asset_url: str


class WorkflowRequest(BaseModel):
    session_id: uuid.UUID
    costume_id: uuid.UUID
    uploaded_asset_url: str


class WorkflowResponse(BaseModel):
    workflow_id: uuid.UUID
    final_asset_url: str
    log_url: str


class PreferenceRequest(BaseModel):
    selection_url: str


class PreferenceResponse(BaseModel):
    workflow_id: uuid.UUID
    selection_url: str


@router.post("/uploads", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    *,
    file: UploadFile = File(...),
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
) -> UploadResponse:
    if not settings.feature_workflows_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not available")

    session_id = uuid.uuid4()
    asset_url = await workflow_service.store_upload(session_id, file)
    return UploadResponse(session_id=session_id, asset_url=asset_url)


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_workflow(
    *,
    payload: WorkflowRequest,
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
    db: Annotated[Database, Depends(get_database)],
) -> WorkflowResponse:
    workflow = await workflow_service.start_workflow(db, payload)
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        final_asset_url=workflow.final_asset_url,
        log_url=workflow.log_url,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
    db: Annotated[Database, Depends(get_database)],
) -> WorkflowResponse:
    workflow = await workflow_service.get_workflow(db, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return WorkflowResponse(
        workflow_id=workflow.workflow_id,
        final_asset_url=workflow.final_asset_url,
        log_url=workflow.log_url,
    )


@router.post("/workflows/{workflow_id}/preferences", response_model=PreferenceResponse)
async def log_preference(
    workflow_id: uuid.UUID,
    payload: PreferenceRequest,
    background_tasks: BackgroundTasks,
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
    db: Annotated[Database, Depends(get_database)],
) -> PreferenceResponse:
    background_tasks.add_task(
        workflow_service.record_preference,
        db,
        workflow_id,
        payload.selection_url,
    )
    return PreferenceResponse(workflow_id=workflow_id, selection_url=payload.selection_url)
