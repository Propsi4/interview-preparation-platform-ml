"""Repository for unified requirements."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.unified_requirements import UnifiedRequirementsModel
from src.db.repositories.base import BaseRepository


class UnifiedRequirementsRepository(BaseRepository[UnifiedRequirementsModel]):
    """Repository for UnifiedRequirementsModel."""

    model = UnifiedRequirementsModel

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_search_query_id(self, search_query_id: int) -> UnifiedRequirementsModel | None:
        """
        Get unified requirements by search query ID.

        Parameters
        ----------
        search_query_id : int
            Search query ID.

        Returns
        -------
        UnifiedRequirementsModel | None
            Unified requirements model or None if not found.
        """
        stmt = select(UnifiedRequirementsModel).where(UnifiedRequirementsModel.search_query_id == search_query_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()
