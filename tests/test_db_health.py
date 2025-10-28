"""Test database connection and health check endpoint."""

import pytest
from fastapi import FastAPI
import httpx

from src.app.factory import create_app


@pytest.fixture
def app() -> FastAPI:
    """Create test app with database."""
    return create_app()


@pytest.mark.asyncio
async def test_health_endpoint(app: FastAPI) -> None:
    """Test basic health endpoint."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_database_health_endpoint(app: FastAPI) -> None:
    """Test database health endpoint."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/healthz/db")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "success" in data["database"]
