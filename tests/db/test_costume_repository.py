import uuid

import pytest

from src.db.database import Database
from src.db.repositories.costumes import CostumeRecord, CostumeRepository


@pytest.mark.asyncio
async def test_costume_upsert_and_list(tmp_path):
    db = Database(f"sqlite+aiosqlite:///{tmp_path/'catalog.db'}")
    await db.create_all()

    repo = CostumeRepository()

    async with db.session() as session:
        costume_id = uuid.uuid4()
        await repo.upsert_costumes(
            session,
            [
                CostumeRecord(
                    id=costume_id,
                    name="Mage Robe",
                    prompt="Generate mage robe",
                    reference_image_url="https://example.com/ref.png",
                    affiliate_link=None,
                )
            ],
        )
        await session.commit()

    async with db.session() as session:
        costumes = await repo.list_active(session)

    assert len(costumes) == 1
    assert costumes[0].name == "Mage Robe"
