"""SQLAlchemy models for the Waifu Material backend."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Boolean, Column, Date, DateTime, Enum, Float,
                        ForeignKey, Integer, String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, mapped_column, relationship


Base = declarative_base()


class WorkflowStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class AssetType(str, enum.Enum):
    uploaded = "uploaded"
    background_removed = "background_removed"
    seedream = "seedream"
    final = "final"


class User(Base):
    __tablename__ = "users"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    last_active = mapped_column(DateTime, default=datetime.utcnow)
    preferences = Column(JSON, nullable=True)
    user_metadata = Column(JSON, nullable=True)

    workflow_runs = relationship("WorkflowRun", back_populates="user")


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
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
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
    user = relationship("User", back_populates="workflow_runs")
    assets = relationship("Asset", back_populates="workflow_run")
    preferences = relationship("WorkflowPreference", back_populates="workflow")


class Asset(Base):
    __tablename__ = "assets"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    asset_type = mapped_column(Enum(AssetType), nullable=False)
    storage_path = mapped_column(Text, nullable=False)
    public_url = mapped_column(Text, nullable=True)
    file_size = mapped_column(BigInteger, nullable=True)
    mime_type = mapped_column(String(100), nullable=True)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    workflow_run = relationship("WorkflowRun", back_populates="assets")


class ProcessingMetrics(Base):
    __tablename__ = "processing_metrics"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    step = mapped_column(String(50), nullable=False)
    started_at = mapped_column(DateTime, nullable=False)
    completed_at = mapped_column(DateTime, nullable=True)
    duration_ms = mapped_column(BigInteger, nullable=True)
    success = mapped_column(Boolean, nullable=False)
    error_message = mapped_column(Text, nullable=True)
    retry_count = mapped_column(Integer, default=0)

    workflow_run = relationship("WorkflowRun")


class CostumePopularity(Base):
    __tablename__ = "costume_popularity"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    costume_id = mapped_column(UUID(as_uuid=True), ForeignKey("costumes.id"), nullable=False)
    date = mapped_column(Date, nullable=False)
    attempt_count = mapped_column(Integer, default=0)
    success_count = mapped_column(Integer, default=0)
    average_processing_time = mapped_column(Float, nullable=True)

    costume = relationship("Costume")


class WorkflowPreference(Base):
    __tablename__ = "workflow_preferences"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=False)
    selection_url = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime, default=datetime.utcnow)

    workflow = relationship("WorkflowRun", back_populates="preferences")
