"""Repository for vacancy interview score models."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

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
