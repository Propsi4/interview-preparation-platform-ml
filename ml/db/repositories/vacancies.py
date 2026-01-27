"""Repository for vacancy models."""

from __future__ import annotations

from typing import Mapping, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.db.models.vacancies import VacancyModel
from ml.db.repositories.base import BaseRepository


class VacancyRepository(BaseRepository[VacancyModel]):
    """Repository for VacancyModel."""

    model = VacancyModel

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with a session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        super().__init__(session)

    async def list_by_search_query_id(self, search_query_id: int) -> list[VacancyModel]:
        """
        List vacancies for a search query.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.

        Returns
        -------
        list[VacancyModel]
            Vacancies for the search query.
        """
        stmt = select(self.model).where(self.model.search_query_id == search_query_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_search_query_id(self, search_query_id: int, **filters: Any) -> int:
        """
        Count vacancies for a search query.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.

        Returns
        -------
        int
            Vacancy count.
        """
        return await self.count_by(search_query_id=search_query_id, **filters)

    async def list_descriptions(self, search_query_id: int) -> list[str]:
        """
        List non-empty vacancy descriptions for a search query.

        Parameters
        ----------
        search_query_id : int
            Search query identifier.

        Returns
        -------
        list[str]
            Vacancy descriptions.
        """
        vacancies = await self.list_by_search_query_id(search_query_id)
        return [vacancy.description for vacancy in vacancies if vacancy.description is not None]

    async def update_details(self, vacancy: VacancyModel, updates: Mapping[str, Any]) -> VacancyModel:
        """
        Update a vacancy with scraped details.

        Parameters
        ----------
        vacancy : VacancyModel
            Vacancy to update.
        updates : Mapping[str, Any]
            Field updates.

        Returns
        -------
        VacancyModel
            Updated vacancy.
        """
        return await self.update(vacancy, updates)
