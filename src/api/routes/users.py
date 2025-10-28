"""User management endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from ...app.dependencies import get_user_service
from ...services.user import UserService

router = APIRouter(tags=["users"])


class SessionRequest(BaseModel):
    session_id: uuid.UUID


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    session_id: uuid.UUID


class UserPreferences(BaseModel):
    preferences: dict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    preferences: Optional[dict] = None
    user_metadata: Optional[dict] = None


@router.post(
    "/users/session",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    *,
    payload: SessionRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SessionResponse:
    """Create or update a user session."""
    user = await user_service.create_or_update(payload.session_id)
    return SessionResponse.model_validate(user)


@router.get("/users/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> SessionResponse:
    """Get user by session ID."""
    user = await user_service.get_by_session(session_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return SessionResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Get user by ID."""
    user = await user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/preferences", response_model=UserResponse)
async def update_preferences(
    user_id: uuid.UUID,
    *,
    payload: UserPreferences,
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    """Update user preferences."""
    user = await user_service.update_preferences(user_id, payload.preferences)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserResponse.model_validate(user)
