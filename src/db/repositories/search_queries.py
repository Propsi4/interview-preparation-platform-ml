"""Repository for search query models."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.search_query import SearchQueryModel
from src.db.repositories.base import BaseRepository
from src.db.repositories.vacancies import VacancyRepository


class SearchQueryRepository(BaseRepository[SearchQueryModel]):
    """Repository for SearchQueryModel."""

    model = SearchQueryModel

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with a session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        super().__init__(session)

    async def update_total_results(self, search_query: SearchQueryModel, total_results: int) -> SearchQueryModel:
        """
        Update total results for a search query.

        Parameters
        ----------
        search_query : SearchQueryModel
            Search query entity.
        total_results : int
            Total results from scraping.

        Returns
        -------
        SearchQueryModel
            Updated entity.
        """
        return await self.update(search_query, {"total_results": total_results})

    async def get_progress(self, search_query_id: int) -> float | None:
        """
        Get progress for a search query.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.
        """
        search_query = await self.get(search_query_id)
        if search_query is None:
            return None
        total_results = search_query.total_results
        processed_results = await VacancyRepository(self._session).count_by_search_query_id(
            search_query_id=search_query_id
        )
        if total_results is None:
            return None
        return round(min(processed_results / total_results, 1.0), 1)

    async def delete(self, search_query_id: int) -> bool:
        """
        Delete a search query and all its related data.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.

        Returns
        -------
        bool
            True if the search query was deleted.
        """
        from sqlalchemy import delete
        from src.db.models.vacancies import VacancyModel
        from src.db.models.vacancy_interview_score import VacancyInterviewScoreModel
        from src.db.models.chat_session import ChatSessionModel

        # Delete related records manually to ensure correctness regardless of DB cascade setup
        await self._session.execute(delete(VacancyModel).where(VacancyModel.search_query_id == search_query_id))
        await self._session.execute(
            delete(VacancyInterviewScoreModel).where(VacancyInterviewScoreModel.search_query_id == search_query_id)
        )
        await self._session.execute(delete(ChatSessionModel).where(ChatSessionModel.search_query_id == search_query_id))

        # Delete the search query itself
        return await self.delete_by_id(search_query_id, commit=True)
