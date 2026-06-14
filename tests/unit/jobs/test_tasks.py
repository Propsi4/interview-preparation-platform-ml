"""
Unit tests for background Celery tasks in src/jobs/tasks/.

Verifies that Celery tasks (unify_requirements, evaluate_vacancy_interview, and
scrape_vacancies_overview) correctly orchestrate database repository calls,
invoke AI agents, and trigger subsequent sub-tasks.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Local imports
from src.agents.implementations.assessment.schemas import VacancyInterviewAssessmentSchema
from src.jobs.tasks.evaluate_vacancy_interview import (
    _normalize_assessment,
    _normalize_score,
    evaluate_vacancy_interview,
)
from src.jobs.tasks.scrape_dou_vacancies_overview import scrape_vacancies_overview
from src.jobs.tasks.unify_requirements import unify_requirements_task
from src.scrapers.schemas.vacancy import VacanciesOverviewSchema


class TestEvaluateVacancyInterviewTask:
    """Test suite for the evaluate_vacancy_interview celery task and its helpers."""

    def test_normalize_score(self) -> None:
        """
        Verify that _normalize_score handles float strings, invalid types, and bounds.

        Returns
        -------
        None
        """
        assert _normalize_score(0.75) == 0.8
        assert _normalize_score("0.4") == 0.4
        assert _normalize_score("invalid") == 0.0
        assert _normalize_score(1.5) == 1.0
        assert _normalize_score(-0.5) == 0.0

    def test_normalize_assessment(self) -> None:
        """
        Verify that _normalize_assessment correctly parses raw DSPy output into schemas.

        Returns
        -------
        None
        """
        # Test input dict
        dict_input = {"score": 0.85, "strong_sides": "A", "weak_sides": "B"}
        res = _normalize_assessment(dict_input)
        assert isinstance(res, VacancyInterviewAssessmentSchema)
        assert res.score == 0.8
        assert res.strong_sides == "A"
        assert res.weak_sides == "B"

        # Test invalid input
        res_empty = _normalize_assessment(None)
        assert res_empty.score == 0.0
        assert res_empty.strong_sides is None
        assert res_empty.weak_sides is None

    @patch("src.jobs.tasks.evaluate_vacancy_interview.VacancyInterviewAssessmentAgent")
    @patch("src.jobs.tasks.evaluate_vacancy_interview.VacancyInterviewScoreRepository")
    def test_evaluate_vacancy_interview_task(
        self,
        mock_repo_cls: MagicMock,
        mock_agent_cls: MagicMock,
        mock_db_connection: MagicMock,
    ) -> None:
        """
        Verify that evaluate_vacancy_interview runs evaluation pipeline and persists the score.

        Parameters
        ----------
        mock_repo_cls : MagicMock
            Mock repository class.
        mock_agent_cls : MagicMock
            Mock assessment agent class.
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        mock_agent = mock_agent_cls.return_value
        mock_prediction = MagicMock()
        mock_prediction.assessment = {
            "score": 0.8,
            "strong_sides": "Java, SQL",
            "weak_sides": "None",
        }
        mock_agent.return_value = mock_prediction

        mock_repo = mock_repo_cls.return_value
        mock_repo.add = AsyncMock()
        mock_repo.commit = AsyncMock()

        # Execute celery task
        assessment = evaluate_vacancy_interview(
            vacancy_description="Required Java and SQL.",
            chat_history=[{"role": "user", "content": "I know SQL"}],
            search_query_id=1,
            chat_session_id="session_123",
            vacancy_id=45,
        )

        assert assessment is not None
        assert assessment.score == 0.8
        assert assessment.strong_sides == "Java, SQL"
        assert assessment.weak_sides == "None"

        mock_repo.add.assert_called_once()
        mock_repo.commit.assert_called_once()


class TestUnifyRequirementsTask:
    """Test suite for the unify_requirements_task celery task."""

    @patch("src.jobs.tasks.unify_requirements.VacancyRepository")
    @patch("src.jobs.tasks.unify_requirements.UnifiedRequirementsRepository")
    @patch("src.jobs.tasks.unify_requirements.RequirementsAggregator")
    def test_unify_requirements_task_success(
        self,
        mock_aggregator_cls: MagicMock,
        mock_unified_repo_cls: MagicMock,
        mock_vacancy_repo_cls: MagicMock,
        mock_db_connection: MagicMock,
    ) -> None:
        """
        Verify that requirements aggregation correctly queries vacancies and persists master list.

        Parameters
        ----------
        mock_aggregator_cls : MagicMock
            Mock requirements aggregator class.
        mock_unified_repo_cls : MagicMock
            Mock unified repo class.
        mock_vacancy_repo_cls : MagicMock
            Mock vacancy repo class.
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        mock_vacancy_repo = mock_vacancy_repo_cls.return_value
        mock_vacancy_repo.list_processed_descriptions = AsyncMock(return_value=["Python skill", "FastAPI skill"])

        mock_unified_repo = mock_unified_repo_cls.return_value
        mock_unified_repo.get_by_search_query_id = AsyncMock(return_value=None)
        async def mock_add(entity):
            entity.id = 1
            return entity
        mock_unified_repo.add = AsyncMock(side_effect=mock_add)
        mock_unified_repo.commit = AsyncMock()

        mock_aggregator = mock_aggregator_cls.return_value
        mock_prediction = MagicMock()
        mock_prediction.aggregated_requirements = "Deduplicated Python and FastAPI master list"
        mock_aggregator.return_value = mock_prediction

        res_id = unify_requirements_task(search_query_id=123)
        assert res_id == 1

        mock_vacancy_repo.list_processed_descriptions.assert_called_once_with(123)
        mock_aggregator.assert_called_once()
        mock_unified_repo.add.assert_called_once()
        mock_unified_repo.commit.assert_called_once()


class TestScrapeVacanciesOverviewTask:
    """Test suite for the scrape_vacancies_overview celery task."""

    @patch("src.jobs.tasks.scrape_dou_vacancies_overview.DouScraper")
    @patch("src.jobs.tasks.scrape_dou_vacancies_overview.SearchQueryRepository")
    @patch("src.jobs.tasks.scrape_dou_vacancies_overview.VacancyRepository")
    @patch("src.jobs.tasks.scrape_dou_vacancies_overview.celery_app")
    def test_scrape_vacancies_overview_task(
        self,
        mock_celery_app: MagicMock,
        mock_vacancy_repo_cls: MagicMock,
        mock_query_repo_cls: MagicMock,
        mock_scraper_cls: MagicMock,
        mock_db_connection: MagicMock,
    ) -> None:
        """
        Verify vacancies overview scrape updates query and enqueues detail scrape tasks.

        Parameters
        ----------
        mock_celery_app : MagicMock
            Mock Celery app.
        mock_vacancy_repo_cls : MagicMock
            Mock vacancy repo.
        mock_query_repo_cls : MagicMock
            Mock query repo.
        mock_scraper_cls : MagicMock
            Mock scraper class.
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        # Mock Scraper Response
        mock_scraper = mock_scraper_cls.return_value
        mock_scraper.arun = AsyncMock(
            return_value=VacanciesOverviewSchema(
                query="Python",
                total_results=5,
                vacancies_urls=["http://dou.ua/1", "http://dou.ua/2"],
            )
        )

        # Mock SearchQueryRepository
        mock_query_repo = mock_query_repo_cls.return_value
        mock_query = MagicMock()
        mock_query.id = 10
        mock_query_repo.get = AsyncMock(return_value=mock_query)
        mock_query_repo.update_total_results = AsyncMock()
        mock_query_repo.commit = AsyncMock()

        # Mock VacancyRepository
        mock_vacancy_repo = mock_vacancy_repo_cls.return_value
        mock_vacancy_repo.add_all = AsyncMock()
        mock_vacancy_repo.flush = AsyncMock()
        mock_vacancy_repo.commit = AsyncMock()

        # Run task
        response = scrape_vacancies_overview(search_query_id=10, query="Python")

        assert response.total_results == 5
        assert len(response.vacancies_urls) == 2

        mock_query_repo.update_total_results.assert_called_once_with(mock_query, 5)
        mock_vacancy_repo.add_all.assert_called_once()
        mock_celery_app.send_task.assert_called()
