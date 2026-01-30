"""Repository for chat session models."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.db.models.chat_session import ChatSessionModel
from ml.db.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSessionModel]):
    """Repository for ChatSessionModel."""

    model = ChatSessionModel

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with a session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        super().__init__(session)

    async def get_by_session_id(self, session_id: str) -> ChatSessionModel | None:
        """
        Fetch a chat session by its external session ID.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        ChatSessionModel | None
            Chat session or None if not found.
        """
        return await self.get_one_by(session_id=session_id)

    async def list_all(self) -> list[ChatSessionModel]:
        """
        List all chat sessions ordered by last update.

        Returns
        -------
        list[ChatSessionModel]
            Chat sessions ordered by updated_at descending.
        """
        stmt = select(self.model).order_by(self.model.updated_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
