"""User repository for session and preference management."""

from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from src.db.models import User


class UserRepository:
    """Repository for User model operations."""

    async def get_by_session(
        self, session: AsyncSession, session_id: uuid.UUID
    ) -> Optional[User]:
        """Get user by session ID."""
        result = await session.execute(
            select(User).where(User.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self, session: AsyncSession, session_id: uuid.UUID
    ) -> User:
        """Create or update user session."""
        user = await self.get_by_session(session, session_id)
        if user:
            user.last_active = datetime.utcnow()
        else:
            user = User(session_id=session_id)
            session.add(user)
        await session.flush()
        return user

    async def update_preferences(
        self, session: AsyncSession, user_id: uuid.UUID, preferences: dict
    ) -> User:
        """Update user preferences."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.preferences = preferences
            await session.flush()
        return user

    async def get_by_id(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> Optional[User]:
        """Get user by ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def delete_old_sessions(
        self, session: AsyncSession, hours_old: int
    ) -> int:
        """Delete sessions older than specified hours."""
        from sqlalchemy import delete
        from datetime import timedelta, datetime as dt

        cutoff = dt.utcnow() - timedelta(hours=hours_old)
        stmt = delete(User).where(User.last_active < cutoff)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount

    async def count_active_sessions(
        self, session: AsyncSession
    ) -> int:
        """Count total active user sessions."""
        result = await session.execute(
            select(func.count(User.id)).select_from(User)
        )
        return result.scalar() or 0
