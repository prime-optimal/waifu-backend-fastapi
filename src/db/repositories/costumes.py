"""Repository for costume metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Costume


@dataclass(slots=True)
class CostumeRecord:
    id: uuid.UUID
    name: str
    prompt: str
    reference_image_url: str
    affiliate_link: str | None
    is_active: bool = True


class CostumeRepository:
    async def list_active(
        self,
        session: AsyncSession,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Costume]:
        result = await session.execute(
            select(Costume)
            .where(Costume.is_active.is_(True))
            .order_by(Costume.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, session: AsyncSession, costume_id: uuid.UUID) -> Costume | None:
        return await session.get(Costume, costume_id)

    async def upsert_costumes(
        self, session: AsyncSession, records: Iterable[CostumeRecord]
    ) -> None:
        for record in records:
            existing = await session.get(Costume, record.id)
            if existing:
                existing.name = record.name
                existing.prompt = record.prompt
                existing.reference_image_url = record.reference_image_url
                existing.affiliate_link = record.affiliate_link
                existing.is_active = record.is_active
            else:
                session.add(
                    Costume(
                        id=record.id,
                        name=record.name,
                        prompt=record.prompt,
                        reference_image_url=record.reference_image_url,
                        affiliate_link=record.affiliate_link,
                        is_active=record.is_active,
                    )
                )
        await session.flush()
