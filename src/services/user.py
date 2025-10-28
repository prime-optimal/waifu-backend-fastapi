"""User session and preferences service."""

from __future__ import annotations

import uuid
from typing import Optional

from ..db.database import Database
from ..db.models import User
from ..db.repositories import UserRepository


class UserService:
    """Service for managing user sessions and preferences."""

    def __init__(
        self,
        database: Database,
        repository: UserRepository | None = None,
    ) -> None:
        self._database = database
        self._repository = repository or UserRepository()

    async def get_by_session(self, session_id: uuid.UUID) -> Optional[User]:
        """Get user by session ID."""
        async with self._database.session() as session:
            return await self._repository.get_by_session(session, session_id)

    async def create_or_update(self, session_id: uuid.UUID) -> User:
        """Create or update user session."""
        async with self._database.session() as session:
            user = await self._repository.create_or_update(session, session_id)
            await session.commit()
            return user

    async def update_preferences(
        self, user_id: uuid.UUID, preferences: dict
    ) -> Optional[User]:
        """Update user preferences."""
        async with self._database.session() as session:
            user = await self._repository.update_preferences(
                session, user_id, preferences
            )
            await session.commit()
            return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        async with self._database.session() as session:
            return await self._repository.get_by_id(session, user_id)
