"""Catalog refresh service."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from ..app.settings import AppSettings
from ..db.database import Database
from ..db.repositories import CostumeRepository
from ..db.repositories.costumes import CostumeRecord

logger = logging.getLogger("waifu.catalog")


@dataclass(slots=True)
class CatalogItem:
    id: uuid.UUID
    name: str
    prompt: str
    reference_image_url: str
    affiliate_link: str | None
    is_active: bool = True


class CatalogDataSource:
    async def fetch(self) -> list[CatalogItem]:  # pragma: no cover - interface
        return []


class CatalogService:
    def __init__(
        self,
        *,
        settings: AppSettings,
        database: Database,
        repository: CostumeRepository | None = None,
        data_source: CatalogDataSource | None = None,
    ) -> None:
        self._settings = settings
        self._database = database
        self._repository = repository or CostumeRepository()
        self._data_source = data_source or CatalogDataSource()
        self.cron_kwargs = self._parse_cron_expression(settings.catalog_refresh_cron)

    @classmethod
    def from_settings(cls, settings: AppSettings, database: Database) -> "CatalogService":
        return cls(settings=settings, database=database)

    async def manual_refresh(self, database: Database | None = None) -> int:
        db = database or self._database
        items = await self._data_source.fetch()
        async with db.session() as session:
            await self._repository.upsert_costumes(session, self._to_records(items))
            await session.commit()
        logger.info("catalog.refresh.completed", extra={"extra_data": {"count": len(items)}})
        return len(items)

    async def scheduled_refresh(self) -> None:
        await self.manual_refresh()

    @staticmethod
    def _to_records(items: list[CatalogItem]) -> list[CostumeRecord]:
        return [
            CostumeRecord(
                id=item.id,
                name=item.name,
                prompt=item.prompt,
                reference_image_url=item.reference_image_url,
                affiliate_link=item.affiliate_link,
                is_active=item.is_active,
            )
            for item in items
        ]

    @staticmethod
    def _parse_cron_expression(expr: str) -> dict[str, str]:
        parts = expr.split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression")
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }
