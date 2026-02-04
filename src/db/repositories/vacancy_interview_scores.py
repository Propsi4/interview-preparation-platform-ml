"""Repository for vacancy interview score models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.db.models.vacancy_interview_score import VacancyInterviewScoreModel
from src.db.repositories.base import BaseRepository


class VacancyInterviewScoreRepository(BaseRepository[VacancyInterviewScoreModel]):
    """Repository for VacancyInterviewScoreModel."""

    model = VacancyInterviewScoreModel

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with a session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        super().__init__(session)

    async def get(self, entity_id: int) -> VacancyInterviewScoreModel | None:
        """
        Fetch a single entity by its primary key.

        Parameters
        ----------
        entity_id : int
            Entity identifier.

        Returns
        -------
        VacancyInterviewScoreModel | None
            Loaded entity or None if not found.
        """
        stmt = (
            select(self.model)
            .options(joinedload(self.model.vacancy))
            .where(self.model.id == entity_id)
        )
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def list_by(self, **filters: Any) -> list[VacancyInterviewScoreModel]:
        """
        Fetch entities matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        list[VacancyInterviewScoreModel]
            Retrieved entities.
        """
        stmt = (
            select(self.model)
            .options(joinedload(self.model.vacancy))
            .filter_by(**filters)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
