"""
Unit tests for the scrapers pipeline in src/jobs/pipelines/scrapers.py.

Verifies vacancy scrape enqueuing, progress calculation, and database error scenarios.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest

# Local imports
from src.api.schemas import ScrapeVacanciesRequestSchema
from src.db.models.search_query import SearchQueryModel
from src.jobs.pipelines.scrapers import enqueue_vacancy_scrape, get_scrape_progress


class TestScrapersPipeline:
    """Test suite for the scrapers pipeline."""

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.scrapers.celery_app.send_task")
    @patch("src.jobs.pipelines.scrapers.SearchQueryRepository")
    @patch("src.jobs.pipelines.scrapers.connect_to_db")
    async def test_enqueue_vacancy_scrape_success(
        self,
        mock_connect_to_db: MagicMock,
        mock_query_repo_cls: MagicMock,
        mock_send_task: MagicMock,
    ) -> None:
        """
        Verify that enqueue_vacancy_scrape adds query to database and sends Celery task.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock database connection manager.
        mock_query_repo_cls : MagicMock
            Mock SearchQueryRepository class.
        mock_send_task : MagicMock
            Mock Celery send_task method.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        mock_query_repo_cls.return_value = mock_repo

        mock_repo.add = AsyncMock()
        mock_repo.commit = AsyncMock()

        # Simulate database auto-generating id
        async def mock_refresh(sq: SearchQueryModel) -> None:
            sq.id = 42

        mock_repo.refresh = AsyncMock(side_effect=mock_refresh)

        payload = ScrapeVacanciesRequestSchema(search_query="Python")
        res = await enqueue_vacancy_scrape(payload)

        assert res.search_query_id == 42
        mock_repo.add.assert_called_once()
        mock_repo.commit.assert_called_once()
        mock_repo.refresh.assert_called_once()
        mock_send_task.assert_called_once_with(
            name="scrapers.dou.scrape_vacancies_overview",
            kwargs={"search_query_id": 42, "query": "Python"},
        )

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.scrapers.SearchQueryRepository")
    @patch("src.jobs.pipelines.scrapers.connect_to_db")
    async def test_get_scrape_progress_not_found(
        self,
        mock_connect_to_db: MagicMock,
        mock_query_repo_cls: MagicMock,
    ) -> None:
        """
        Verify that get_scrape_progress raises ValueError when search query does not exist.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock database connection.
        mock_query_repo_cls : MagicMock
            Mock SearchQueryRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
        mock_query_repo_cls.return_value = mock_repo

        with pytest.raises(ValueError, match="Search query not found"):
            await get_scrape_progress(999)

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.scrapers.VacancyRepository")
    @patch("src.jobs.pipelines.scrapers.SearchQueryRepository")
    @patch("src.jobs.pipelines.scrapers.connect_to_db")
    async def test_get_scrape_progress_success(
        self,
        mock_connect_to_db: MagicMock,
        mock_query_repo_cls: MagicMock,
        mock_vacancy_repo_cls: MagicMock,
    ) -> None:
        """
        Verify progress calculation logic including limits and rounding.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock database connection.
        mock_query_repo_cls : MagicMock
            Mock SearchQueryRepository.
        mock_vacancy_repo_cls : MagicMock
            Mock VacancyRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_query_repo = MagicMock()
        query = SearchQueryModel(id=12, query="Python", total_results=15)
        mock_query_repo.get = AsyncMock(return_value=query)
        mock_query_repo_cls.return_value = mock_query_repo

        mock_vacancy_repo = MagicMock()
        mock_vacancy_repo.count_by_search_query_id = AsyncMock(return_value=6)
        mock_vacancy_repo_cls.return_value = mock_vacancy_repo

        progress_res = await get_scrape_progress(12)

        assert progress_res.search_query_id == 12
        assert progress_res.progress == 0.4
        assert progress_res.total_results == 15
        assert progress_res.processed_results == 6
        mock_vacancy_repo.count_by_search_query_id.assert_called_once_with(12, scrapped=True)
