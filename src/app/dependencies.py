"""FastAPI dependency helpers."""

from __future__ import annotations

from .settings import AppSettings, get_settings
from ..db.database import Database
from ..services.catalog import CatalogService
from ..services.workflow import WorkflowService


def get_app_settings() -> AppSettings:
    return get_settings()


def get_database() -> Database:
    settings = get_app_settings()
    return Database(settings.database_url)


def get_workflow_service() -> WorkflowService:
    settings = get_app_settings()
    db = get_database()
    return WorkflowService.from_settings(settings, db)


def get_catalog_service() -> CatalogService:
    settings = get_app_settings()
    db = get_database()
    return CatalogService.from_settings(settings, db)
