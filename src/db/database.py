"""Database utilities built around SQLAlchemy's async engine."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base


class Database:
    def __init__(
        self, url: str, *, engine_factory: Callable[[str], AsyncEngine] | None = None
    ) -> None:
        self._engine_factory = engine_factory or create_async_engine
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

        # Clean URL by removing problematic SSL parameters for asyncpg
        self._url = self._clean_url(url)

    def _clean_url(self, url: str) -> str:
        """Clean URL by removing problematic parameters that cause connection issues."""
        if "postgresql+asyncpg" in url:
            # Remove channel_binding and problematic SSL parameters for asyncpg
            import re

            # Remove channel_binding parameter
            url = re.sub(r"&?channel_binding=[^&]*", "", url)

            # Remove or modify SSL parameters
            url = re.sub(r"&?sslmode=[^&]*", "", url)

            # Clean up URL structure
            if url.endswith("?") or url.endswith("&"):
                url = url.rstrip("?&")

            return url

        return url

    def _connect_args(self) -> dict:
        if self._url.startswith("sqlite+"):
            return {"check_same_thread": False}

        # Handle PostgreSQL connection arguments for asyncpg
        if self._url.startswith("postgresql+asyncpg") or self._url.startswith(
            "postgresql+psycopg"
        ):
            args = {}

            # For asyncpg, we need to handle SSL parameters properly
            if "sslmode=require" in self._url or "sslmode=verify-full" in self._url:
                args["ssl"] = "require"
            elif "sslmode=disable" in self._url:
                args["ssl"] = False

            return args

        return {}

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = self._engine_factory(
                self._url,
                future=True,
                echo=False,
                connect_args=self._connect_args(),
            )
        return self._engine

    @property
    def sessionmaker(self) -> async_sessionmaker[AsyncSession]:
        if self._sessionmaker is None:
            self._sessionmaker = async_sessionmaker(self.engine, expire_on_commit=False)
        return self._sessionmaker

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async_session = self.sessionmaker()
        async with async_session as session:
            yield session

    async def create_all(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def verify_connection(self) -> dict[str, Any]:
        """Test database connectivity by executing a simple query.

        Returns:
            dict with 'success' (bool) and 'error' (str | None) keys.
        """
        try:
            async with self.session() as session:
                await session.execute(text("SELECT 1"))
                return {"success": True, "error": None}
        except Exception as e:
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}",
                "error_type": type(e).__name__,
            }

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
