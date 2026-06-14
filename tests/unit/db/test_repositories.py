"""
Unit tests for database repositories in src/db/repositories/.

Verifies CRUD operations on BaseRepository and custom query executions
in all subclasses using mocked SQLAlchemy sessions.
"""

# Standart library imports
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from src.db.models.base import Base
from src.db.models.chat_message import ChatMessageModel
from src.db.models.chat_session import ChatSessionModel
from src.db.models.search_query import SearchQueryModel
from src.db.models.unified_requirements import UnifiedRequirementsModel
from src.db.models.vacancies import VacancyModel
from src.db.models.vacancy_interview_score import VacancyInterviewScoreModel
from src.db.repositories.base import BaseRepository
from src.db.repositories.chat_messages import ChatMessageRepository
from src.db.repositories.chat_sessions import ChatSessionRepository
from src.db.repositories.search_queries import SearchQueryRepository
from src.db.repositories.unified_requirements import UnifiedRequirementsRepository
from src.db.repositories.vacancies import VacancyRepository
from src.db.repositories.vacancy_interview_scores import VacancyInterviewScoreRepository


# A simple dummy model subclassing Base for repository testing
class DummyModel(Base):
    """Dummy SQLAlchemy model for testing BaseRepository."""

    __tablename__ = "dummy_table"


class TestBaseRepository:
    """Test suite for the BaseRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_get_entity(self) -> None:
        """
        Verify that get calls session.get with the correct model class.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.get = AsyncMock(return_value=DummyModel())

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entity = await repo.get(42)
        assert isinstance(entity, DummyModel)
        mock_session.get.assert_called_once_with(DummyModel, 42)

    @pytest.mark.asyncio
    async def test_list_entities(self) -> None:
        """
        Verify that list executes select query with correct limit and offset.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [DummyModel(), DummyModel()]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entities = await repo.list(offset=10, limit=20)
        assert len(entities) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_one_by(self) -> None:
        """
        Verify get_one_by executes query with correct filters.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.one_or_none.return_value = DummyModel()
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entity = await repo.get_one_by(id=123)
        assert isinstance(entity, DummyModel)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by(self) -> None:
        """
        Verify list_by executes query with correct filters.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [DummyModel()]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entities = await repo.list_by(id=123)
        assert len(entities) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by(self) -> None:
        """
        Verify count_by executes correct count query.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        count = await repo.count_by(id=123)
        assert count == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_entity(self) -> None:
        """
        Verify adding a new entity and optional commit.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entity = DummyModel()
        added = await repo.add(entity, commit=True)
        assert added == entity
        mock_session.add.assert_called_once_with(entity)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_all_entities(self) -> None:
        """
        Verify adding multiple entities and optional commit.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entities = [DummyModel(), DummyModel()]
        added = await repo.add_all(entities, commit=True)
        assert added == entities
        mock_session.add_all.assert_called_once_with(entities)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_entity(self) -> None:
        """
        Verify updating an entity in-memory and optional commit.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entity = DummyModel()
        # Set a dummy field dynamically since DummyModel has no fields
        entity.some_field = "old"  # type: ignore[attr-defined]
        updated = await repo.update(entity, {"some_field": "new"}, commit=True)
        assert updated.some_field == "new"  # type: ignore[attr-defined]
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_entity(self) -> None:
        """
        Verify deleting an entity and optional commit.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        entity = DummyModel()
        await repo.delete(entity, commit=True)
        mock_session.delete.assert_called_once_with(entity)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_id(self) -> None:
        """
        Verify delete_by_id executes delete statement and returns boolean status.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        deleted = await repo.delete_by_id(123, commit=True)
        assert deleted is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_controls(self) -> None:
        """
        Verify transaction control methods (commit, flush, refresh) call session methods.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        repo = BaseRepository[DummyModel](mock_session)
        repo.model = DummyModel

        await repo.commit()
        await repo.flush()
        entity = DummyModel()
        await repo.refresh(entity)

        mock_session.commit.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(entity)


class TestSearchQueryRepository:
    """Test suite for the SearchQueryRepository operations."""

    @pytest.mark.asyncio
    async def test_update_total_results(self) -> None:
        """
        Verify SearchQueryRepository.update_total_results updates total_results.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = SearchQueryRepository(mock_session)
        query = SearchQueryModel(query="Python", total_results=10)

        with patch.object(repo, "update", AsyncMock(return_value=query)) as mock_update:
            updated = await repo.update_total_results(query, 20)
            assert updated == query
            mock_update.assert_called_once_with(query, {"total_results": 20})

    @pytest.mark.asyncio
    async def test_get_progress_query_not_found(self) -> None:
        """
        Verify get_progress returns None when query is not found.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = SearchQueryRepository(mock_session)

        with patch.object(repo, "get", AsyncMock(return_value=None)):
            progress = await repo.get_progress(123)
            assert progress is None

    @pytest.mark.asyncio
    async def test_get_progress_total_results_none(self) -> None:
        """
        Verify get_progress returns None when total_results is None.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = SearchQueryRepository(mock_session)
        query = SearchQueryModel(query="Python", total_results=None)

        with patch.object(repo, "get", AsyncMock(return_value=query)), patch(
            "src.db.repositories.search_queries.VacancyRepository.count_by_search_query_id",
            AsyncMock(return_value=0),
        ):
            progress = await repo.get_progress(123)
            assert progress is None

    @pytest.mark.asyncio
    async def test_get_progress_success(self) -> None:
        """
        Verify get_progress calculates correct rounded progress.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = SearchQueryRepository(mock_session)
        query = SearchQueryModel(query="Python", total_results=10)

        with patch.object(repo, "get", AsyncMock(return_value=query)), patch(
            "src.db.repositories.search_queries.VacancyRepository.count_by_search_query_id",
            AsyncMock(return_value=3),
        ):
            progress = await repo.get_progress(123)
            assert progress == 0.3

    @pytest.mark.asyncio
    async def test_delete_query(self) -> None:
        """
        Verify delete query deletes search query and related tables.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        repo = SearchQueryRepository(mock_session)

        with patch.object(repo, "delete_by_id", AsyncMock(return_value=True)) as mock_delete_by_id:
            status = await repo.delete(123)
            assert status is True
            assert mock_session.execute.call_count == 3
            mock_delete_by_id.assert_called_once_with(123, commit=True)


class TestChatMessageRepository:
    """Test suite for the ChatMessageRepository."""

    @pytest.mark.asyncio
    async def test_list_by_session_id(self) -> None:
        """
        Verify list_by_session_id orders messages by created_at.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        msg = ChatMessageModel(session_id="session_123", role="user", content="hello")
        mock_result.scalars.return_value.all.return_value = [msg]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ChatMessageRepository(mock_session)
        messages = await repo.list_by_session_id("session_123")
        assert len(messages) == 1
        assert messages[0] == msg
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_session_id(self) -> None:
        """
        Verify count_by_session_id returns total message count.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = ChatMessageRepository(mock_session)

        with patch.object(repo, "count_by", AsyncMock(return_value=15)) as mock_count:
            count = await repo.count_by_session_id("session_123")
            assert count == 15
            mock_count.assert_called_once_with(session_id="session_123")


class TestChatSessionRepository:
    """Test suite for the ChatSessionRepository."""

    @pytest.mark.asyncio
    async def test_get_by_session_id(self) -> None:
        """
        Verify get_by_session_id fetches single session.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = ChatSessionRepository(mock_session)
        session_model = ChatSessionModel(session_id="session_123")

        with patch.object(repo, "get_one_by", AsyncMock(return_value=session_model)) as mock_get_one:
            res = await repo.get_by_session_id("session_123")
            assert res == session_model
            mock_get_one.assert_called_once_with(session_id="session_123")

    @pytest.mark.asyncio
    async def test_list_all_sessions(self) -> None:
        """
        Verify list_all returns sessions ordered by updated_at descending.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        session_model = ChatSessionModel(session_id="session_123")
        mock_result.scalars.return_value.all.return_value = [session_model]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ChatSessionRepository(mock_session)
        sessions = await repo.list_all()
        assert len(sessions) == 1
        assert sessions[0] == session_model
        mock_session.execute.assert_called_once()


class TestUnifiedRequirementsRepository:
    """Test suite for the UnifiedRequirementsRepository."""

    @pytest.mark.asyncio
    async def test_get_by_search_query_id(self) -> None:
        """
        Verify get_by_search_query_id executes query for search_query_id.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        req = UnifiedRequirementsModel(search_query_id=123, requirements="some reqs")
        mock_result.scalars.return_value.first.return_value = req
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = UnifiedRequirementsRepository(mock_session)
        res = await repo.get_by_search_query_id(123)
        assert res == req
        mock_session.execute.assert_called_once()


class TestVacancyRepository:
    """Test suite for the VacancyRepository operations."""

    @pytest.mark.asyncio
    async def test_list_by_search_query_id(self) -> None:
        """
        Verify listing vacancies filtered by search query id.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        v1 = VacancyModel()
        mock_result.scalars.return_value.all.return_value = [v1]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = VacancyRepository(mock_session)
        vacancies = await repo.list_by_search_query_id(search_query_id=123)

        assert len(vacancies) == 1
        assert vacancies[0] == v1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_search_query_id(self) -> None:
        """
        Verify count_by_search_query_id counts vacancies with filters.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = VacancyRepository(mock_session)

        with patch.object(repo, "count_by", AsyncMock(return_value=42)) as mock_count:
            res = await repo.count_by_search_query_id(123, scrapped=True)
            assert res == 42
            mock_count.assert_called_once_with(search_query_id=123, scrapped=True)

    @pytest.mark.asyncio
    async def test_list_descriptions(self) -> None:
        """
        Verify extraction of non-empty vacancy descriptions.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        v1 = VacancyModel()
        v1.description = "Python developer needed"
        v2 = VacancyModel()
        v2.description = None
        v3 = VacancyModel()
        v3.description = "Go developer needed"

        repo = VacancyRepository(mock_session)

        with patch.object(repo, "list_by_search_query_id", AsyncMock(return_value=[v1, v2, v3])):
            descriptions = await repo.list_descriptions(123)
            assert descriptions == ["Python developer needed", "Go developer needed"]

    @pytest.mark.asyncio
    async def test_list_processed_descriptions_fallback(self) -> None:
        """
        Verify processed descriptions list with fallback to raw descriptions.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        v1 = VacancyModel()
        v1.description = "Raw 1"
        v1.processed_description = "Processed 1"
        v2 = VacancyModel()
        v2.description = "Raw 2"
        v2.processed_description = None
        v3 = VacancyModel()
        v3.description = None
        v3.processed_description = None

        repo = VacancyRepository(mock_session)

        with patch.object(repo, "list_by_search_query_id", AsyncMock(return_value=[v1, v2, v3])):
            descriptions = await repo.list_processed_descriptions(123)
            assert descriptions == ["Processed 1", "Raw 2"]

    @pytest.mark.asyncio
    async def test_update_details(self) -> None:
        """
        Verify update_details updates the vacancy attributes.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        repo = VacancyRepository(mock_session)
        vacancy = VacancyModel()

        with patch.object(repo, "update", AsyncMock(return_value=vacancy)) as mock_update:
            res = await repo.update_details(vacancy, {"title": "new title"})
            assert res == vacancy
            mock_update.assert_called_once_with(vacancy, {"title": "new title"})


class TestVacancyInterviewScoreRepository:
    """Test suite for the VacancyInterviewScoreRepository."""

    @pytest.mark.asyncio
    async def test_get_with_options(self) -> None:
        """
        Verify get uses joinedload options and executes query.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        score = VacancyInterviewScoreModel(id=45)
        mock_result.scalars.return_value.one_or_none.return_value = score
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = VacancyInterviewScoreRepository(mock_session)
        res = await repo.get(45)
        assert res == score
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by_with_options(self) -> None:
        """
        Verify list_by uses joinedload options and filters.

        Returns
        -------
        None
        """
        mock_session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        score = VacancyInterviewScoreModel(id=45)
        mock_result.scalars.return_value.all.return_value = [score]
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = VacancyInterviewScoreRepository(mock_session)
        res = await repo.list_by(chat_session_id="session_abc")
        assert len(res) == 1
        assert res[0] == score
        mock_session.execute.assert_called_once()
