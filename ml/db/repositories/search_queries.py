"""Repository for search query models."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ml.db.models.search_query import SearchQueryModel
from ml.db.repositories.base import BaseRepository
from ml.db.repositories.vacancies import VacancyRepository


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
        processed_results = await VacancyRepository(self._session).count_by_search_query_id(search_query_id=search_query_id)
        if total_results is None:
            return None
        return round(min(processed_results / total_results, 1.0), 1)
