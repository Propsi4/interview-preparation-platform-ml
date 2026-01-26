"""Repository abstractions and base CRUD implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Mapping, Sequence, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ml.db.models.base import Base

TModel = TypeVar("TModel", bound=Base)


class ReadRepository(ABC, Generic[TModel]):
    """Read-only repository interface."""

    @abstractmethod
    async def get(self, entity_id: int) -> TModel | None:
        """
        Fetch a single entity by its primary key.

        Parameters
        ----------
        entity_id : int
            Entity identifier.

        Returns
        -------
        TModel | None
            Loaded entity or None if not found.
        """

    @abstractmethod
    async def list(self, offset: int = 0, limit: int = 100) -> list[TModel]:
        """
        Fetch a page of entities.

        Parameters
        ----------
        offset : int, optional
            Offset of the first record.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        list[TModel]
            Retrieved entities.
        """

    @abstractmethod
    async def get_one_by(self, **filters: Any) -> TModel | None:
        """
        Fetch a single entity matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        TModel | None
            Loaded entity or None if not found.
        """

    @abstractmethod
    async def list_by(self, **filters: Any) -> list[TModel]:
        """
        Fetch entities matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        list[TModel]
            Retrieved entities.
        """

    @abstractmethod
    async def count_by(self, **filters: Any) -> int:
        """
        Count entities matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        int
            Count of matching entities.
        """


class WriteRepository(ABC, Generic[TModel]):
    """Write-only repository interface."""

    @abstractmethod
    async def add(self, entity: TModel, *, commit: bool = False) -> TModel:
        """
        Add a new entity to the session.

        Parameters
        ----------
        entity : TModel
            Entity to add.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        TModel
            Added entity.
        """

    @abstractmethod
    async def add_all(self, entities: Sequence[TModel], *, commit: bool = False) -> Sequence[TModel]:
        """
        Add multiple entities to the session.

        Parameters
        ----------
        entities : Sequence[TModel]
            Entities to add.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        Sequence[TModel]
            Added entities.
        """

    @abstractmethod
    async def update(self, entity: TModel, data: Mapping[str, Any], *, commit: bool = False) -> TModel:
        """
        Update entity fields in-memory.

        Parameters
        ----------
        entity : TModel
            Entity to update.
        data : Mapping[str, Any]
            Fields to update.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        TModel
            Updated entity.
        """

    @abstractmethod
    async def delete(self, entity: TModel, *, commit: bool = False) -> None:
        """
        Delete an entity from the session.

        Parameters
        ----------
        entity : TModel
            Entity to delete.
        commit : bool, optional
            Whether to commit the session.
        """

    @abstractmethod
    async def delete_by_id(self, entity_id: int, *, commit: bool = False) -> bool:
        """
        Delete an entity by its primary key.

        Parameters
        ----------
        entity_id : int
            Entity identifier.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        bool
            True if an entity was deleted.
        """

    @abstractmethod
    async def commit(self) -> None:
        """
        Commit current transaction.

        Returns
        -------
        None
        """

    @abstractmethod
    async def flush(self) -> None:
        """
        Flush pending changes.

        Returns
        -------
        None
        """

    @abstractmethod
    async def refresh(self, entity: TModel) -> None:
        """
        Refresh entity state from the database.

        Parameters
        ----------
        entity : TModel
            Entity to refresh.

        Returns
        -------
        None
        """


class BaseRepository(ReadRepository[TModel], WriteRepository[TModel]):
    """Generic async CRUD repository for SQLAlchemy models."""

    model: type[TModel]

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with an async session.

        Parameters
        ----------
        session : AsyncSession
            SQLAlchemy async session.
        """
        self._session = session

    async def get(self, entity_id: int) -> TModel | None:
        """
        Fetch a single entity by its primary key.

        Parameters
        ----------
        entity_id : int
            Entity identifier.

        Returns
        -------
        TModel | None
            Loaded entity or None if not found.
        """
        return await self._session.get(self.model, entity_id)

    async def list(self, offset: int = 0, limit: int = 100) -> list[TModel]:
        """
        Fetch a page of entities.

        Parameters
        ----------
        offset : int, optional
            Offset of the first record.
        limit : int, optional
            Maximum number of records to return.

        Returns
        -------
        list[TModel]
            Retrieved entities.
        """
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_one_by(self, **filters: Any) -> TModel | None:
        """
        Fetch a single entity matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        TModel | None
            Loaded entity or None if not found.
        """
        stmt = select(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return result.scalars().one_or_none()

    async def list_by(self, **filters: Any) -> list[TModel]:
        """
        Fetch entities matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        list[TModel]
            Retrieved entities.
        """
        stmt = select(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by(self, **filters: Any) -> int:
        """
        Count entities matching filters.

        Parameters
        ----------
        **filters : Any
            SQLAlchemy filter-by parameters.

        Returns
        -------
        int
            Count of matching entities.
        """
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def add(self, entity: TModel, *, commit: bool = False) -> TModel:
        """
        Add a new entity to the session.

        Parameters
        ----------
        entity : TModel
            Entity to add.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        TModel
            Added entity.
        """
        self._session.add(entity)
        if commit:
            await self._session.commit()
        return entity

    async def add_all(self, entities: Sequence[TModel], *, commit: bool = False) -> Sequence[TModel]:
        """
        Add multiple entities to the session.

        Parameters
        ----------
        entities : Sequence[TModel]
            Entities to add.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        Sequence[TModel]
            Added entities.
        """
        self._session.add_all(list(entities))
        if commit:
            await self._session.commit()
        return entities

    async def update(self, entity: TModel, data: Mapping[str, Any], *, commit: bool = False) -> TModel:
        """
        Update entity fields in-memory.

        Parameters
        ----------
        entity : TModel
            Entity to update.
        data : Mapping[str, Any]
            Fields to update.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        TModel
            Updated entity.
        """
        for key, value in data.items():
            setattr(entity, key, value)
        if commit:
            await self._session.commit()
        return entity

    async def delete(self, entity: TModel, *, commit: bool = False) -> None:
        """
        Delete an entity from the session.

        Parameters
        ----------
        entity : TModel
            Entity to delete.
        commit : bool, optional
            Whether to commit the session.
        """
        await self._session.delete(entity)
        if commit:
            await self._session.commit()

    async def delete_by_id(self, entity_id: int, *, commit: bool = False) -> bool:
        """
        Delete an entity by its primary key.

        Parameters
        ----------
        entity_id : int
            Entity identifier.
        commit : bool, optional
            Whether to commit the session.

        Returns
        -------
        bool
            True if an entity was deleted.
        """
        stmt = delete(self.model).where(self.model.id == entity_id)
        result = await self._session.execute(stmt)
        if commit:
            await self._session.commit()
        return result.rowcount is not None and result.rowcount > 0

    async def commit(self) -> None:
        """
        Commit current transaction.

        Returns
        -------
        None
        """
        await self._session.commit()

    async def flush(self) -> None:
        """
        Flush pending changes.

        Returns
        -------
        None
        """
        await self._session.flush()

    async def refresh(self, entity: TModel) -> None:
        """
        Refresh entity state from the database.

        Parameters
        ----------
        entity : TModel
            Entity to refresh.

        Returns
        -------
        None
        """
        await self._session.refresh(entity)
