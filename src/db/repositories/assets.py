"""Repository for workflow asset management."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Asset, AssetType


class AssetRepository:
    """Repository providing CRUD operations for workflow assets."""

    async def create_asset(
        self,
        session: AsyncSession,
        *,
        workflow_run_id: uuid.UUID,
        asset_type: AssetType,
        storage_path: str,
        public_url: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> Asset:
        asset = Asset(
            workflow_run_id=workflow_run_id,
            asset_type=asset_type,
            storage_path=storage_path,
            public_url=public_url,
            file_size=file_size,
            mime_type=mime_type,
        )
        session.add(asset)
        await session.flush()
        return asset

    async def get_by_workflow(
        self,
        session: AsyncSession,
        workflow_run_id: uuid.UUID,
    ) -> list[Asset]:
        result = await session.execute(
            select(Asset)
            .where(Asset.workflow_run_id == workflow_run_id)
            .order_by(Asset.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        session: AsyncSession,
        asset_id: uuid.UUID,
    ) -> Asset | None:
        return await session.get(Asset, asset_id)

    async def get_public_url(
        self,
        session: AsyncSession,
        asset_id: uuid.UUID,
    ) -> str | None:
        result = await session.execute(
            select(Asset.public_url).where(Asset.id == asset_id)
        )
        return result.scalar_one_or_none()

    async def update_asset_metadata(
        self,
        session: AsyncSession,
        asset_id: uuid.UUID,
        *,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> Asset | None:
        update_data: dict[str, Any] = {}
        if file_size is not None:
            update_data["file_size"] = file_size
        if mime_type is not None:
            update_data["mime_type"] = mime_type

        if not update_data:
            return await self.get_by_id(session, asset_id)

        stmt = update(Asset).where(Asset.id == asset_id).values(**update_data)
        result = await session.execute(stmt)
        if result.rowcount == 0:
            return None

        await session.flush()
        return await self.get_by_id(session, asset_id)

    async def delete_asset(
        self,
        session: AsyncSession,
        asset_id: uuid.UUID,
    ) -> bool:
        stmt = delete(Asset).where(Asset.id == asset_id)
        result = await session.execute(stmt)
        await session.flush()
        return bool(result.rowcount)
