"""SQLAlchemy models for the Waifu Material backend."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Enum, ForeignKey, String,
                        Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, mapped_column, relationship


Base = declarative_base()


class WorkflowStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class Costume(Base):
    __tablename__ = "costumes"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String(length=120), nullable=False)
    prompt = mapped_column(Text, nullable=False)
    reference_image_url = mapped_column(Text, nullable=False)
    affiliate_link = mapped_column(Text, nullable=True)
    is_active = mapped_column(Boolean, default=True, nullable=False)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workflows = relationship("WorkflowRun", back_populates="costume")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_session = mapped_column(UUID(as_uuid=True), nullable=False)
    costume_id = mapped_column(UUID(as_uuid=True), ForeignKey("costumes.id"), nullable=False)
    status = mapped_column(Enum(WorkflowStatus), default=WorkflowStatus.pending, nullable=False)
    uploaded_asset_url = mapped_column(Text, nullable=False)
    background_asset_url = mapped_column(Text, nullable=True)
    seedream_asset_url = mapped_column(Text, nullable=True)
    final_asset_url = mapped_column(Text, nullable=True)
    log_object_path = mapped_column(Text, nullable=True)
    detail = Column(JSON, nullable=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    costume = relationship("Costume", back_populates="workflows")
    preferences = relationship("WorkflowPreference", back_populates="workflow")


class WorkflowPreference(Base):
    __tablename__ = "workflow_preferences"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    selection_url = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    workflow = relationship("WorkflowRun", back_populates="preferences")
