"""Repository for chat message models."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.chat_message import ChatMessageModel
from src.db.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessageModel]):
    """Repository for ChatMessageModel."""

    model = ChatMessageModel

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with a session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        super().__init__(session)

    async def list_by_session_id(self, session_id: str) -> list[ChatMessageModel]:
        """
        List messages for a session ordered by creation time.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        list[ChatMessageModel]
            Messages ordered by created_at ascending.
        """
        stmt = select(self.model).where(self.model.session_id == session_id).order_by(self.model.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_session_id(self, session_id: str) -> int:
        """
        Count messages for a session.

        Parameters
        ----------
        session_id : str
            Chat session identifier.

        Returns
        -------
        int
            Message count.
        """
        return await self.count_by(session_id=session_id)
