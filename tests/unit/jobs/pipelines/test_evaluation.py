"""
Unit tests for the evaluation pipeline in src/jobs/pipelines/evaluation.py.

Verifies vacancy loading, chat history retrieval, and Celery task dispatching.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from langchain_core.messages import HumanMessage

# Local imports
from src.db.models.vacancies import VacancyModel
from src.jobs.pipelines.evaluation import dispatch_vacancy_assessments


class TestEvaluationPipeline:
    """Test suite for the evaluation pipeline."""

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.evaluation.celery_app.send_task")
    @patch("src.jobs.pipelines.evaluation.langchain_messages_to_dicts")
    @patch("src.jobs.pipelines.evaluation.history_manager.get_messages_for_session")
    @patch("src.jobs.pipelines.evaluation.VacancyRepository")
    @patch("src.jobs.pipelines.evaluation.connect_to_db")
    async def test_dispatch_vacancy_assessments_success(
        self,
        mock_connect_to_db: MagicMock,
        mock_vacancy_repo_cls: MagicMock,
        mock_get_messages: AsyncMock,
        mock_to_dicts: MagicMock,
        mock_send_task: MagicMock,
    ) -> None:
        """
        Verify that dispatch_vacancy_assessments properly dispatches Celery tasks.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock database connection manager.
        mock_vacancy_repo_cls : MagicMock
            Mock VacancyRepository class.
        mock_get_messages : AsyncMock
            Mock ConversationHistoryManager.get_messages_for_session.
        mock_to_dicts : MagicMock
            Mock langchain_messages_to_dicts converter.
        mock_send_task : MagicMock
            Mock Celery send_task method.

        Returns
        -------
        None
        """
        # Set up mock database session and repo
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        mock_vacancy_repo_cls.return_value = mock_repo

        v1 = VacancyModel(id=1, description="Need Python developer")
        v2 = VacancyModel(id=2, description="")  # Empty description, should be skipped
        v3 = VacancyModel(id=3, description=None)  # None description, should be skipped
        v4 = VacancyModel(id=4, description="Need Go developer")
        mock_repo.list_by_search_query_id = AsyncMock(return_value=[v1, v2, v3, v4])

        # Set up history and serialization mocks
        mock_history = [HumanMessage(content="Hello")]
        mock_get_messages.return_value = mock_history
        mock_to_dicts.return_value = [{"role": "user", "content": "Hello"}]

        dispatched = await dispatch_vacancy_assessments("session_abc", 12)

        # We should dispatch only v1 and v4 (2 tasks)
        assert dispatched == 2
        assert mock_send_task.call_count == 2

        # Check call arguments
        mock_send_task.assert_any_call(
            name="assessment.evaluate_vacancy_interview",
            kwargs={
                "vacancy_id": 1,
                "vacancy_description": "Need Python developer",
                "chat_history": [{"role": "user", "content": "Hello"}],
                "search_query_id": 12,
                "chat_session_id": "session_abc",
            },
        )
        mock_send_task.assert_any_call(
            name="assessment.evaluate_vacancy_interview",
            kwargs={
                "vacancy_id": 4,
                "vacancy_description": "Need Go developer",
                "chat_history": [{"role": "user", "content": "Hello"}],
                "search_query_id": 12,
                "chat_session_id": "session_abc",
            },
        )
