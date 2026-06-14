"""
Unit tests for the FastAPI application routes in src/api/.

Verifies health checks, session details retrieval, chat routes, history
management, scraper controls, evaluation dispatching, and speech transcription/synthesis
including WebSocket streaming using FastAPI's TestClient and mocked service layers.
"""

# Standart library imports
import base64
from datetime import datetime
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

# Local imports
from src.api.main import app
from src.api.schemas import ProgressResponseSchema, ScrapeVacanciesResponseSchema
from src.conversation_history.schemas import ChatSessionOverviewSchema
from src.db.models.chat_message import ChatMessageModel
from src.db.models.chat_session import ChatSessionModel
from src.db.models.search_query import SearchQueryModel
from src.db.models.vacancy_interview_score import VacancyInterviewScoreModel
from src.jobs.pipelines.chat import InterviewAlreadyFinishedError


@pytest.fixture(autouse=True)
def mock_health_check() -> Generator[None, None, None]:
    """
    Prevent db connection checks in lifespan start on client creation.

    Yields
    ------
    None
    """
    with patch(
        "src.conversation_history.manager.ConversationHistoryManager.check_health",
        AsyncMock(return_value=True),
    ):
        yield


class TestAPIRoutes:
    """Test suite for FastAPI endpoints."""

    def test_health_endpoint_healthy(self) -> None:
        """
        Verify that /health returns correct response when service is healthy.

        Returns
        -------
        None
        """
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "healthy" in data["message"]

    def test_health_endpoint_unhealthy(self) -> None:
        """
        Verify that /health returns error response when service is unhealthy.

        Returns
        -------
        None
        """
        with patch(
            "src.conversation_history.manager.ConversationHistoryManager.check_health",
            AsyncMock(return_value=False),
        ):
            with TestClient(app) as client:
                response = client.get("/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "error"
                assert "not healthy" in data["message"]

    # --- Chat Router ---

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    @patch("src.api.routes.chat.run_interview")
    def test_chat_with_interview_agent_success(
        self, mock_run_interview: MagicMock, mock_ensure_not_finished: MagicMock
    ) -> None:
        """
        Verify chat route executes successfully and returns expected schema.

        Parameters
        ----------
        mock_run_interview : MagicMock
            Mock interview run logic.
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        mock_ensure_not_finished.return_value = None
        mock_run_interview.return_value = {
            "response": "Hello candidate",
            "interview_finished": False,
        }

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "Hello candidate"
            assert data["interview_finished"] is False

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    def test_chat_with_interview_agent_finished_conflict(self, mock_ensure_not_finished: MagicMock) -> None:
        """
        Verify that chat route returns 409 status if the interview is already finished.

        Parameters
        ----------
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        mock_ensure_not_finished.side_effect = InterviewAlreadyFinishedError("Already finished")

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 409
            assert "Already finished" in response.json()["detail"]

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    def test_chat_with_interview_agent_exception(self, mock_ensure_not_finished: MagicMock) -> None:
        """
        Verify that chat route returns 500 status on unexpected exceptions.

        Parameters
        ----------
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        mock_ensure_not_finished.side_effect = Exception("DB Down")

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 500
            assert "Failed to run interview" in response.json()["detail"]

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    @patch("src.api.routes.chat.stream_interview")
    def test_chat_with_interview_agent_stream_success(
        self, mock_stream_interview: MagicMock, mock_ensure_not_finished: MagicMock
    ) -> None:
        """
        Verify streaming chat endpoint returns StreamingResponse.

        Parameters
        ----------
        mock_stream_interview : MagicMock
            Mock stream interview pipeline.
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        from fastapi.responses import StreamingResponse
        mock_ensure_not_finished.return_value = None

        async def mock_generator() -> AsyncGenerator[str, None]:
            yield "data: hello\n\n"

        mock_stream_interview.return_value = StreamingResponse(
            mock_generator(),
            media_type="text/event-stream",
        )

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc/stream",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    def test_chat_with_interview_agent_stream_conflict(self, mock_ensure_not_finished: MagicMock) -> None:
        """
        Verify that streaming chat route returns 409 status if finished.

        Parameters
        ----------
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        mock_ensure_not_finished.side_effect = InterviewAlreadyFinishedError("Already finished")

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc/stream",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 409
            assert "Already finished" in response.json()["detail"]

    @patch("src.api.routes.chat.ensure_interview_not_finished")
    def test_chat_with_interview_agent_stream_exception(self, mock_ensure_not_finished: MagicMock) -> None:
        """
        Verify that streaming chat route returns 500 status on unexpected exceptions.

        Parameters
        ----------
        mock_ensure_not_finished : MagicMock
            Mock finish verification.

        Returns
        -------
        None
        """
        mock_ensure_not_finished.side_effect = Exception("DB Down")

        with TestClient(app) as client:
            response = client.post(
                "/chat/interview/session_abc/stream",
                json={"search_query_id": 12, "query": "Hello"},
            )
            assert response.status_code == 500
            assert "Failed to stream interview" in response.json()["detail"]

    # --- Chat History Router ---

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.chat_history.ChatMessageRepository")
    @patch("src.api.routes.chat_history.ChatSessionRepository")
    async def test_get_messages_for_session_success(
        self,
        mock_session_repo_cls: MagicMock,
        mock_message_repo_cls: MagicMock,
    ) -> None:
        """
        Verify retrieve messages for session returns valid schema.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock session repo.
        mock_message_repo_cls : MagicMock
            Mock message repo.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        mock_sess.get_by_session_id = AsyncMock(
            return_value=ChatSessionModel(
                session_id="session_abc",
                title="Sess Title",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                price=0.01,
                interview_finished=False,
                evaluated=False,
                search_query_id=1,
            )
        )
        mock_session_repo_cls.return_value = mock_sess

        mock_msg = MagicMock()
        mock_msg.list_by_session_id = AsyncMock(
            return_value=[
                ChatMessageModel(
                    id=10,
                    role="user",
                    content="Hello",
                    created_at=datetime.utcnow(),
                )
            ]
        )
        mock_message_repo_cls.return_value = mock_msg

        with TestClient(app) as client:
            response = client.get("/conversation_history/session/session_abc")
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_abc"
            assert len(data["messages"]) == 1
            assert data["messages"][0]["content"] == "Hello"

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.chat_history.ChatSessionRepository")
    async def test_get_messages_for_session_not_found(
        self,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify retrieve messages returns error status response when session not found.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock session repo.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        mock_sess.get_by_session_id = AsyncMock(return_value=None)
        mock_session_repo_cls.return_value = mock_sess

        with TestClient(app) as client:
            response = client.get("/conversation_history/session/session_abc")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Session session_abc not found" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.get_all_sessions")
    def test_list_chat_sessions(self, mock_get_all: MagicMock) -> None:
        """
        Verify that GET /conversation_history/sessions returns list of sessions overview.

        Parameters
        ----------
        mock_get_all : MagicMock
            Mock get all sessions method.

        Returns
        -------
        None
        """
        mock_overview = ChatSessionOverviewSchema(
            session_id="session_123",
            search_query_id=1,
            title="Interview Title",
            created_at=datetime(2026, 6, 8, 12, 0, 0),
            updated_at=datetime(2026, 6, 8, 13, 0, 0),
            total_messages=4,
            price=0.01,
            interview_finished=False,
            evaluated=False,
        )
        mock_get_all.return_value = [mock_overview]

        with TestClient(app) as client:
            response = client.get("/conversation_history/sessions")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["session_id"] == "session_123"

    @patch("src.api.routes.chat_history.history_manager.get_all_sessions")
    def test_list_chat_sessions_error(self, mock_get_all: MagicMock) -> None:
        """
        Verify list sessions failure returns error response.

        Parameters
        ----------
        mock_get_all : MagicMock
            Mock get all sessions method.

        Returns
        -------
        None
        """
        mock_get_all.side_effect = Exception("DB connection lost")

        with TestClient(app) as client:
            response = client.get("/conversation_history/sessions")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to list" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.update_session_title")
    def test_rename_chat_session_success(self, mock_update: MagicMock) -> None:
        """
        Verify rename chat session successfully returns status ok.

        Parameters
        ----------
        mock_update : MagicMock
            Mock update session title method.

        Returns
        -------
        None
        """
        mock_update.return_value = True

        with TestClient(app) as client:
            response = client.patch("/conversation_history/session/session_abc/title?new_title=NewName")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "renamed to 'NewName'" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.update_session_title")
    def test_rename_chat_session_failure(self, mock_update: MagicMock) -> None:
        """
        Verify rename failure returns error status response.

        Parameters
        ----------
        mock_update : MagicMock
            Mock update session title.

        Returns
        -------
        None
        """
        mock_update.return_value = False

        with TestClient(app) as client:
            response = client.patch("/conversation_history/session/session_abc/title?new_title=NewName")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to rename" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.update_session_title")
    def test_rename_chat_session_exception(self, mock_update: MagicMock) -> None:
        """
        Verify rename exception returns error status response.

        Parameters
        ----------
        mock_update : MagicMock
            Mock update session title.

        Returns
        -------
        None
        """
        mock_update.side_effect = Exception("Write error")

        with TestClient(app) as client:
            response = client.patch("/conversation_history/session/session_abc/title?new_title=NewName")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to rename" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.get_session_price")
    def test_get_session_price_success(self, mock_get_price: MagicMock) -> None:
        """
        Verify that GET /conversation_history/session/{session_id}/price returns accumulated price.

        Parameters
        ----------
        mock_get_price : MagicMock
            Mock get session price method.

        Returns
        -------
        None
        """
        mock_get_price.return_value = 0.045

        with TestClient(app) as client:
            response = client.get("/conversation_history/session/session_abc/price")
            assert response.status_code == 200
            assert response.json() == 0.045

    @patch("src.api.routes.chat_history.history_manager.get_session_price")
    def test_get_session_price_error(self, mock_get_price: MagicMock) -> None:
        """
        Verify price exception returns 0.0.

        Parameters
        ----------
        mock_get_price : MagicMock
            Mock get session price.

        Returns
        -------
        None
        """
        mock_get_price.side_effect = Exception("Price calc error")

        with TestClient(app) as client:
            response = client.get("/conversation_history/session/session_abc/price")
            assert response.status_code == 200
            assert response.json() == 0.0

    @patch("src.api.routes.chat_history.history_manager.delete_chat_by_session_id")
    def test_delete_session_history_success(self, mock_delete: MagicMock) -> None:
        """
        Verify delete session history successfully returns status ok.

        Parameters
        ----------
        mock_delete : MagicMock
            Mock delete session history.

        Returns
        -------
        None
        """
        mock_delete.return_value = True

        with TestClient(app) as client:
            response = client.delete("/conversation_history/session/session_abc")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "deleted" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.delete_chat_by_session_id")
    def test_delete_session_history_failure(self, mock_delete: MagicMock) -> None:
        """
        Verify delete session history failure returns error status.

        Parameters
        ----------
        mock_delete : MagicMock
            Mock delete session history.

        Returns
        -------
        None
        """
        mock_delete.return_value = False

        with TestClient(app) as client:
            response = client.delete("/conversation_history/session/session_abc")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to delete" in data["message"]

    @patch("src.api.routes.chat_history.history_manager.delete_chat_by_session_id")
    def test_delete_session_history_exception(self, mock_delete: MagicMock) -> None:
        """
        Verify delete session history exception returns error status.

        Parameters
        ----------
        mock_delete : MagicMock
            Mock delete session history.

        Returns
        -------
        None
        """
        mock_delete.side_effect = Exception("Delete error")

        with TestClient(app) as client:
            response = client.delete("/conversation_history/session/session_abc")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "Failed to delete" in data["message"]

    # --- Scrapers Router ---

    @patch("src.api.routes.scrapers.enqueue_vacancy_scrape")
    def test_scrape_vacancies(self, mock_enqueue: MagicMock) -> None:
        """
        Verify enqueuing a vacancy scrape job.

        Parameters
        ----------
        mock_enqueue : MagicMock
            Mock enqueue_vacancy_scrape.

        Returns
        -------
        None
        """
        mock_enqueue.return_value = ScrapeVacanciesResponseSchema(search_query_id=123)

        with TestClient(app) as client:
            response = client.post("/scrapers/scrape", json={"search_query": "Python"})
            assert response.status_code == 202
            assert response.json()["search_query_id"] == 123

    @patch("src.api.routes.scrapers.get_scrape_progress")
    def test_get_progress_success(self, mock_progress: MagicMock) -> None:
        """
        Verify scraping progress retrieval.

        Parameters
        ----------
        mock_progress : MagicMock
            Mock get_scrape_progress.

        Returns
        -------
        None
        """
        mock_progress.return_value = ProgressResponseSchema(
            search_query_id=123,
            progress=0.5,
            total_results=10,
            processed_results=5,
        )

        with TestClient(app) as client:
            response = client.get("/scrapers/progress/123")
            assert response.status_code == 200
            assert response.json()["progress"] == 0.5

    @patch("src.api.routes.scrapers.get_scrape_progress")
    def test_get_progress_not_found(self, mock_progress: MagicMock) -> None:
        """
        Verify get progress returns 404 if search query does not exist.

        Parameters
        ----------
        mock_progress : MagicMock
            Mock get_scrape_progress.

        Returns
        -------
        None
        """
        mock_progress.side_effect = ValueError("Query not found")

        with TestClient(app) as client:
            response = client.get("/scrapers/progress/999")
            assert response.status_code == 404
            assert "Query not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.scrapers.SearchQueryRepository")
    async def test_list_search_queries(self, mock_repo_cls: MagicMock) -> None:
        """
        Verify list of search queries returns correct list of queries.

        Parameters
        ----------
        mock_repo_cls : MagicMock
            Mock SearchQueryRepository.

        Returns
        -------
        None
        """
        mock_repo = MagicMock()
        mock_repo.list = AsyncMock(
            return_value=[
                SearchQueryModel(
                    id=1,
                    query="Python",
                    total_results=10,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            ]
        )
        mock_repo_cls.return_value = mock_repo

        with TestClient(app) as client:
            response = client.get("/scrapers/queries")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["query"] == "Python"

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.scrapers.SearchQueryRepository")
    async def test_delete_search_query_success(self, mock_repo_cls: MagicMock) -> None:
        """
        Verify delete search query returns 204.

        Parameters
        ----------
        mock_repo_cls : MagicMock
            Mock SearchQueryRepository.

        Returns
        -------
        None
        """
        mock_repo = MagicMock()
        mock_repo.delete = AsyncMock(return_value=True)
        mock_repo_cls.return_value = mock_repo

        with TestClient(app) as client:
            response = client.delete("/scrapers/queries/123")
            assert response.status_code == 204

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.scrapers.SearchQueryRepository")
    async def test_delete_search_query_not_found(self, mock_repo_cls: MagicMock) -> None:
        """
        Verify delete query returns 404 if query not found.

        Parameters
        ----------
        mock_repo_cls : MagicMock
            Mock SearchQueryRepository.

        Returns
        -------
        None
        """
        mock_repo = MagicMock()
        mock_repo.delete = AsyncMock(return_value=False)
        mock_repo_cls.return_value = mock_repo

        with TestClient(app) as client:
            response = client.delete("/scrapers/queries/999")
            assert response.status_code == 404
            assert "Search query not found" in response.json()["detail"]

    # --- Evaluation Router ---

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.dispatch_vacancy_assessments")
    @patch("src.api.routes.evaluation.VacancyInterviewScoreRepository")
    @patch("src.api.routes.evaluation.ChatSessionRepository")
    async def test_dispatch_evaluation_success(
        self,
        mock_session_repo_cls: MagicMock,
        mock_score_repo_cls: MagicMock,
        mock_dispatch: AsyncMock,
    ) -> None:
        """
        Verify dispatch evaluation runs and updates evaluated flag.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.
        mock_score_repo_cls : MagicMock
            Mock VacancyInterviewScoreRepository.
        mock_dispatch : AsyncMock
            Mock dispatch_vacancy_assessments.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        session_model = ChatSessionModel(
            session_id="session_abc",
            interview_finished=True,
            evaluated=False,
        )
        mock_sess.get_by_session_id = AsyncMock(return_value=session_model)
        mock_sess.commit = AsyncMock()
        mock_session_repo_cls.return_value = mock_sess

        mock_score = MagicMock()
        mock_score.count_by = AsyncMock(return_value=0)
        mock_score_repo_cls.return_value = mock_score

        mock_dispatch.return_value = 5

        with TestClient(app) as client:
            response = client.post(
                "/evaluation/evaluate",
                json={"chat_session_id": "session_abc", "search_query_id": 12},
            )
            assert response.status_code == 202
            assert response.json()["dispatched_tasks"] == 5
            assert session_model.evaluated is True

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.ChatSessionRepository")
    async def test_dispatch_evaluation_session_not_found(
        self,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify dispatch evaluation returns 404 when session not found.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        mock_sess.get_by_session_id = AsyncMock(return_value=None)
        mock_session_repo_cls.return_value = mock_sess

        with TestClient(app) as client:
            response = client.post(
                "/evaluation/evaluate",
                json={"chat_session_id": "session_abc", "search_query_id": 12},
            )
            assert response.status_code == 404
            assert "Session session_abc not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.ChatSessionRepository")
    async def test_dispatch_evaluation_not_finished(
        self,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify dispatch evaluation returns 400 when session is not finished.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        session_model = ChatSessionModel(
            session_id="session_abc",
            interview_finished=False,
        )
        mock_sess.get_by_session_id = AsyncMock(return_value=session_model)
        mock_session_repo_cls.return_value = mock_sess

        with TestClient(app) as client:
            response = client.post(
                "/evaluation/evaluate",
                json={"chat_session_id": "session_abc", "search_query_id": 12},
            )
            assert response.status_code == 400
            assert "Interview is not finished" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.ChatSessionRepository")
    async def test_dispatch_evaluation_already_evaluated(
        self,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify dispatch evaluation returns 409 when session evaluated is True.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        session_model = ChatSessionModel(
            session_id="session_abc",
            interview_finished=True,
            evaluated=True,
        )
        mock_sess.get_by_session_id = AsyncMock(return_value=session_model)
        mock_session_repo_cls.return_value = mock_sess

        with TestClient(app) as client:
            response = client.post(
                "/evaluation/evaluate",
                json={"chat_session_id": "session_abc", "search_query_id": 12},
            )
            assert response.status_code == 409
            assert "Evaluation already dispatched" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.VacancyInterviewScoreRepository")
    @patch("src.api.routes.evaluation.ChatSessionRepository")
    async def test_dispatch_evaluation_scores_exist(
        self,
        mock_session_repo_cls: MagicMock,
        mock_score_repo_cls: MagicMock,
    ) -> None:
        """
        Verify dispatch evaluation returns 409 when scores exist.

        Parameters
        ----------
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.
        mock_score_repo_cls : MagicMock
            Mock VacancyInterviewScoreRepository.

        Returns
        -------
        None
        """
        mock_sess = MagicMock()
        session_model = ChatSessionModel(
            session_id="session_abc",
            interview_finished=True,
            evaluated=False,
        )
        mock_sess.get_by_session_id = AsyncMock(return_value=session_model)
        mock_session_repo_cls.return_value = mock_sess

        mock_score = MagicMock()
        mock_score.count_by = AsyncMock(return_value=1)
        mock_score_repo_cls.return_value = mock_score

        with TestClient(app) as client:
            response = client.post(
                "/evaluation/evaluate",
                json={"chat_session_id": "session_abc", "search_query_id": 12},
            )
            assert response.status_code == 409
            assert "Evaluation results already exist" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_db_connection")
    @patch("src.api.routes.evaluation.VacancyInterviewScoreRepository")
    async def test_list_evaluation_results(self, mock_score_repo_cls: MagicMock) -> None:
        """
        Verify listing evaluation results for a session returns details list.

        Parameters
        ----------
        mock_score_repo_cls : MagicMock
            Mock VacancyInterviewScoreRepository.

        Returns
        -------
        None
        """
        mock_score = MagicMock()
        score_model = VacancyInterviewScoreModel(
            id=1,
            search_query_id=10,
            chat_session_id="session_abc",
            score=0.85,
            strong_sides="Strong logic",
            weak_sides="No speech",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        score_model.search_query = SearchQueryModel(query="Python Dev")
        score_model.vacancy = MagicMock(id=5, title="Dev", company="Google", url="url", location="Kyiv")
        mock_score.list_by = AsyncMock(return_value=[score_model])
        mock_score_repo_cls.return_value = mock_score

        with TestClient(app) as client:
            response = client.get("/evaluation/session/session_abc/results")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["score"] == 0.85
            assert data[0]["vacancy_company"] == "Google"

    # --- Speech Router ---

    @patch("src.api.routes.speech.transcribe_audio")
    def test_transcribe_speech_audio_success(self, mock_transcribe: MagicMock) -> None:
        """
        Verify transcribing speech audio returns text transcript.

        Parameters
        ----------
        mock_transcribe : MagicMock
            Mock transcribe_audio service.

        Returns
        -------
        None
        """
        mock_transcribe.return_value = "hello transcription"

        with TestClient(app) as client:
            response = client.post(
                "/speech/transcribe",
                files={"audio_file": ("test.wav", b"fake audio content")},
                data={"language": "en"},
            )
            assert response.status_code == 200
            assert response.json()["text"] == "hello transcription"

    @patch("src.api.routes.speech.transcribe_audio")
    def test_transcribe_speech_audio_error(self, mock_transcribe: MagicMock) -> None:
        """
        Verify transcribe failure returns 500.

        Parameters
        ----------
        mock_transcribe : MagicMock
            Mock transcribe_audio.

        Returns
        -------
        None
        """
        mock_transcribe.side_effect = Exception("Whisper error")

        with TestClient(app) as client:
            response = client.post(
                "/speech/transcribe",
                files={"audio_file": ("test.wav", b"fake audio content")},
            )
            assert response.status_code == 500
            assert "Failed to transcribe audio" in response.json()["detail"]

    @patch("src.api.routes.speech.stream_tts_audio")
    def test_synthesize_speech_audio_success(self, mock_stream_tts: MagicMock) -> None:
        """
        Verify TTS synthesizes text to file response.

        Parameters
        ----------
        mock_stream_tts : MagicMock
            Mock stream_tts_audio.

        Returns
        -------
        None
        """
        mock_stream_tts.return_value = [b"chunk1", b"chunk2"]

        with TestClient(app) as client:
            response = client.post("/speech/tts", json={"text": "hello synthesis"})
            assert response.status_code == 200
            assert len(response.content) > 0

    @patch("src.api.routes.speech.stream_tts_audio")
    def test_synthesize_speech_audio_error(self, mock_stream_tts: MagicMock) -> None:
        """
        Verify TTS failure returns 500.

        Parameters
        ----------
        mock_stream_tts : MagicMock
            Mock stream_tts_audio.

        Returns
        -------
        None
        """
        mock_stream_tts.side_effect = Exception("TTS error")

        with TestClient(app) as client:
            response = client.post("/speech/tts", json={"text": "hello synthesis"})
            assert response.status_code == 500
            assert "Failed to synthesize speech" in response.json()["detail"]

    @patch("src.api.routes.speech.stream_tts_audio")
    @patch("src.api.routes.speech.iter_interview_events")
    @patch("src.api.routes.speech.transcribe_audio")
    @patch("src.api.routes.speech.ensure_interview_not_finished")
    def test_speech_stream_websocket_success(
        self,
        mock_ensure: MagicMock,
        mock_transcribe: MagicMock,
        mock_iter_events: MagicMock,
        mock_stream_tts: MagicMock,
    ) -> None:
        """
        Verify speech WebSocket stream processes start, audio, and end frames.

        Parameters
        ----------
        mock_ensure : MagicMock
            Mock ensure_interview_not_finished.
        mock_transcribe : MagicMock
            Mock transcribe_audio.
        mock_iter_events : MagicMock
            Mock iter_interview_events.
        mock_stream_tts : MagicMock
            Mock stream_tts_audio.

        Returns
        -------
        None
        """
        mock_ensure.return_value = None
        mock_transcribe.return_value = "Hello AI"

        async def mock_events(*args: Any, **kwargs: Any) -> AsyncGenerator[dict[str, Any], None]:
            yield {"type": "reasoning", "data": {"token": "Thinking..."}}
            yield {"type": "answer", "data": {"token": "Response token"}}
            yield {"type": "complete", "data": {"response": "Response token"}}

        mock_iter_events.side_effect = mock_events
        mock_stream_tts.return_value = [b"audio_chunk_1", b"audio_chunk_2"]

        with TestClient(app) as client:
            with client.websocket_connect("/speech/stream") as ws:
                # Send start frame
                ws.send_json({
                    "type": "start",
                    "session_id": "session_123",
                    "search_query_id": 1,
                    "audio_file_name": "test.wav",
                    "audio_format": "wav",
                    "language_code": "en",
                    "tts_enabled": True,
                })

                # Receive info event
                info_ev = ws.receive_json()
                assert info_ev["type"] == "info"

                # Send audio frame
                ws.send_json({
                    "type": "audio",
                    "chunk": base64.b64encode(b"abcd").decode("ascii"),
                })

                # Send end frame
                ws.send_json({
                    "type": "end",
                })

                # Receive transcript event
                transcript_ev = ws.receive_json()
                assert transcript_ev["type"] == "transcript"
                assert transcript_ev["data"]["text"] == "Hello AI"

                # Receive reasoning event
                reasoning_ev = ws.receive_json()
                assert reasoning_ev["type"] == "reasoning"

                # Receive answer event
                answer_ev = ws.receive_json()
                assert answer_ev["type"] == "answer"

                # Receive complete event
                complete_ev = ws.receive_json()
                assert complete_ev["type"] == "complete"

                # Receive audio_chunk events
                ac1 = ws.receive_json()
                assert ac1["type"] == "audio_chunk"
                ac2 = ws.receive_json()
                assert ac2["type"] == "audio_chunk"

                # Receive final info event
                final_info = ws.receive_json()
                assert final_info["type"] == "info"

    def test_speech_stream_websocket_unsupported_frame(self) -> None:
        """
        Verify unsupported frame type terminates websocket with error.

        Returns
        -------
        None
        """
        with TestClient(app) as client:
            with client.websocket_connect("/speech/stream") as ws:
                ws.send_json({"type": "invalid_type"})
                err = ws.receive_json()
                assert err["type"] == "error"
                with pytest.raises(WebSocketDisconnect):
                    ws.receive_json()

    def test_speech_stream_websocket_no_start_frame_raises(self) -> None:
        """
        Verify sending audio or end frame without start frame raises error.

        Returns
        -------
        None
        """
        with TestClient(app) as client:
            with client.websocket_connect("/speech/stream") as ws:
                ws.send_json({
                    "type": "audio",
                    "chunk": "YWJjZA==",
                })
                err = ws.receive_json()
                assert err["type"] == "error"
                with pytest.raises(WebSocketDisconnect):
                    ws.receive_json()
