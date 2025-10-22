"""Database utilities built around SQLAlchemy's async engine."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

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
        self._url = url

    def _connect_args(self) -> dict:
        if self._url.startswith("sqlite+"):
            return {"check_same_thread": False}
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

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
