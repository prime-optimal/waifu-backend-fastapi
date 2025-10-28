"""Application factory and dependency wiring."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from .dependencies import (
    get_analytics_service,
    get_app_settings,
    get_catalog_service,
    get_database,
    get_user_service,
    get_workflow_service,
)
from .settings import AppSettings, get_settings
from ..api.routes import analytics, catalog, users, workflows
from ..db.database import Database
from ..observability.logger import configure_logging
from ..services.analytics import AnalyticsService
from ..services.catalog import CatalogService
from ..services.user import UserService
from ..services.workflow import WorkflowService


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Create a configured FastAPI instance."""

    settings = settings or get_settings()
    configure_logging()
    logger = logging.getLogger("waifu.app")

    db = Database(settings.database_url)

    workflow_service = WorkflowService.from_settings(settings, db)
    catalog_service = CatalogService.from_settings(settings, db)
    user_service = UserService(db)
    analytics_service = AnalyticsService(db)

    scheduler = AsyncIOScheduler()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await db.create_all()
        scheduler.add_job(
            catalog_service.scheduled_refresh,
            trigger="cron",
            id="catalog-refresh",
            replace_existing=True,
            **catalog_service.cron_kwargs,
        )
        scheduler.start()
        logger.info("Application startup complete")
        try:
            yield
        finally:
            scheduler.shutdown(wait=False)
            await workflow_service.close()
            await db.dispose()
            logger.info("Application shutdown complete")

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.dependency_overrides[get_app_settings] = lambda: settings
    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service
    app.dependency_overrides[get_catalog_service] = lambda: catalog_service
    app.dependency_overrides[get_user_service] = lambda: user_service
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service

    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(catalog.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")

    @app.get("/healthz")
    async def health() -> dict[str, Any]:
        return {"status": "ok"}

    @app.get("/healthz/db")
    async def health_db() -> dict[str, Any]:
        """Health check endpoint that verifies database connection."""
        result = await db.verify_connection()
        return {
            "status": "ok" if result["success"] else "database_unavailable",
            "database": result,
        }

    return app
