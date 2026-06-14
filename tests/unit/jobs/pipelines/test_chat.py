"""
Unit tests for the chat pipeline in src/jobs/pipelines/chat.py.

Verifies interview checks, LLM configs, payload building, and both
sync and streaming execution paths using mocked database sessions and DSPy.
"""

# Standart library imports
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import dspy  # type: ignore[import-untyped]
import pytest
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

# Local imports
from src.api.schemas import InterviewChatRequestSchema, ConfigableLLMRequestSchema
from src.db.models.chat_session import ChatSessionModel
from src.db.models.search_query import SearchQueryModel
from src.db.models.unified_requirements import UnifiedRequirementsModel
from src.jobs.pipelines.chat import (
    InterviewAlreadyFinishedError,
    build_request_payload,
    ensure_interview_not_finished,
    iter_interview_events,
    load_job_title,
    load_unified_requirements,
    resolve_llm_config,
    run_interview,
    stream_interview,
)


class TestChatPipeline:
    """Test suite for the chat pipeline."""

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.ChatSessionRepository")
    @patch("src.jobs.pipelines.chat.connect_to_db")
    async def test_ensure_interview_not_finished_active(
        self,
        mock_connect_to_db: MagicMock,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify ensure_interview_not_finished passes silently when active or missing.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock DB connection.
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        mock_repo.get_by_session_id = AsyncMock(return_value=None)
        mock_session_repo_cls.return_value = mock_repo

        # Should not raise exception
        await ensure_interview_not_finished("session_abc")

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.ChatSessionRepository")
    @patch("src.jobs.pipelines.chat.connect_to_db")
    async def test_ensure_interview_not_finished_raises(
        self,
        mock_connect_to_db: MagicMock,
        mock_session_repo_cls: MagicMock,
    ) -> None:
        """
        Verify ensure_interview_not_finished raises error when session is finished.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock DB connection.
        mock_session_repo_cls : MagicMock
            Mock ChatSessionRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        mock_session_model = ChatSessionModel(interview_finished=True)
        mock_repo.get_by_session_id = AsyncMock(return_value=mock_session_model)
        mock_session_repo_cls.return_value = mock_repo

        with pytest.raises(InterviewAlreadyFinishedError, match="Interview already finished"):
            await ensure_interview_not_finished("session_abc")

    def test_resolve_llm_config_defaults(self) -> None:
        """
        Verify resolve_llm_config defaults to global config when overrides are absent.

        Returns
        -------
        None
        """
        payload = InterviewChatRequestSchema(search_query_id=1, query="hello")
        model, temp, kwargs = resolve_llm_config(payload)
        assert model is not None
        assert temp is not None
        assert isinstance(kwargs, dict)

    def test_resolve_llm_config_overrides(self) -> None:
        """
        Verify resolve_llm_config merges request payload overrides properly.

        Returns
        -------
        None
        """
        override = ConfigableLLMRequestSchema(
            llm_model="custom-gpt",
            llm_temperature=0.1,
            additional_llm_kwargs={"presence_penalty": 0.5},
        )
        payload = InterviewChatRequestSchema(search_query_id=1, query="hello", llm_config_override=override)
        model, temp, kwargs = resolve_llm_config(payload)
        assert model == "custom-gpt"
        assert temp == 0.1
        assert kwargs["presence_penalty"] == 0.5

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.UnifiedRequirementsRepository")
    @patch("src.jobs.pipelines.chat.connect_to_db")
    async def test_load_unified_requirements(
        self,
        mock_connect_to_db: MagicMock,
        mock_unified_repo_cls: MagicMock,
    ) -> None:
        """
        Verify load_unified_requirements fetches and extracts requirements correctly.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock DB connection.
        mock_unified_repo_cls : MagicMock
            Mock UnifiedRequirementsRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        reqs = UnifiedRequirementsModel(requirements="Python, SQL")
        mock_repo.get_by_search_query_id = AsyncMock(return_value=reqs)
        mock_unified_repo_cls.return_value = mock_repo

        res = await load_unified_requirements(12)
        assert res == "Python, SQL"

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.SearchQueryRepository")
    @patch("src.jobs.pipelines.chat.connect_to_db")
    async def test_load_job_title(
        self,
        mock_connect_to_db: MagicMock,
        mock_search_repo_cls: MagicMock,
    ) -> None:
        """
        Verify load_job_title fetches search query value.

        Parameters
        ----------
        mock_connect_to_db : MagicMock
            Mock DB connection.
        mock_search_repo_cls : MagicMock
            Mock SearchQueryRepository.

        Returns
        -------
        None
        """
        mock_session = MagicMock()
        mock_connect_to_db.return_value.__aenter__.return_value = mock_session

        mock_repo = MagicMock()
        sq = SearchQueryModel(query="Go Developer")
        mock_repo.get = AsyncMock(return_value=sq)
        mock_search_repo_cls.return_value = mock_repo

        res = await load_job_title(12)
        assert res == "Go Developer"

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.load_unified_requirements")
    @patch("src.jobs.pipelines.chat.load_job_title")
    @patch("src.jobs.pipelines.chat.history_manager.get_messages_for_session")
    async def test_build_request_payload_success(
        self,
        mock_get_messages: AsyncMock,
        mock_load_title: AsyncMock,
        mock_load_reqs: AsyncMock,
    ) -> None:
        """
        Verify build_request_payload successfully constructs turn schema with history.

        Parameters
        ----------
        mock_get_messages : AsyncMock
            Mock ConversationHistoryManager.get_messages_for_session.
        mock_load_title : AsyncMock
            Mock load_job_title.
        mock_load_reqs : AsyncMock
            Mock load_unified_requirements.

        Returns
        -------
        None
        """
        mock_get_messages.return_value = [HumanMessage(content="Hello")]
        mock_load_title.return_value = "Python Developer"
        mock_load_reqs.return_value = "Requirement list"

        payload = InterviewChatRequestSchema(search_query_id=1, query="new turn")
        req = await build_request_payload("session_abc", payload)

        assert req.job_title == "Python Developer"
        assert req.unified_requirements == "Requirement list"
        assert req.query == "new turn"
        assert len(req.chat_history) == 1

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.load_job_title")
    async def test_build_request_payload_missing_title_raises(
        self,
        mock_load_title: AsyncMock,
    ) -> None:
        """
        Verify build_request_payload raises ValueError if job title is missing.

        Parameters
        ----------
        mock_load_title : AsyncMock
            Mock load_job_title.

        Returns
        -------
        None
        """
        mock_load_title.return_value = None
        payload = InterviewChatRequestSchema(search_query_id=1, query="new turn")
        with pytest.raises(ValueError, match="Job title not found"):
            await build_request_payload("session_abc", payload)

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.load_unified_requirements")
    @patch("src.jobs.pipelines.chat.load_job_title")
    async def test_build_request_payload_missing_reqs_raises(
        self,
        mock_load_title: AsyncMock,
        mock_load_reqs: AsyncMock,
    ) -> None:
        """
        Verify build_request_payload raises ValueError if requirements are missing.

        Parameters
        ----------
        mock_load_title : AsyncMock
            Mock load_job_title.
        mock_load_reqs : AsyncMock
            Mock load_unified_requirements.

        Returns
        -------
        None
        """
        mock_load_title.return_value = "Title"
        mock_load_reqs.return_value = None
        payload = InterviewChatRequestSchema(search_query_id=1, query="new turn")
        with pytest.raises(ValueError, match="Unified requirements not found"):
            await build_request_payload("session_abc", payload)

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.persist_chat_and_cost")
    @patch("src.jobs.pipelines.chat.extract_request_cost")
    @patch("src.jobs.pipelines.chat.build_request_payload")
    @patch("src.jobs.pipelines.chat.InterviewAgent")
    @patch("src.jobs.pipelines.chat.dspy.LM")
    async def test_run_interview_success(
        self,
        mock_lm_cls: MagicMock,
        mock_agent_cls: MagicMock,
        mock_build_payload: AsyncMock,
        mock_extract_cost: MagicMock,
        mock_persist: AsyncMock,
    ) -> None:
        """
        Verify run_interview executes synchronously, gets agent predictions, and saves results.

        Parameters
        ----------
        mock_lm_cls : MagicMock
            Mock DSPy LM.
        mock_agent_cls : MagicMock
            Mock InterviewAgent class.
        mock_build_payload : AsyncMock
            Mock build_request_payload.
        mock_extract_cost : MagicMock
            Mock extract_request_cost.
        mock_persist : AsyncMock
            Mock persist_chat_and_cost.

        Returns
        -------
        None
        """
        mock_build_payload.return_value = MagicMock(
            job_title="Dev",
            unified_requirements="Reqs",
            chat_history=[],
            query="hello",
        )
        mock_agent = MagicMock()
        mock_prediction = MagicMock()
        mock_prediction.interview_finished = True
        mock_prediction.response = "Hello Candidate!"
        mock_agent.return_value = mock_prediction
        mock_agent_cls.return_value = mock_agent

        mock_lm = MagicMock()
        mock_lm_cls.return_value = mock_lm
        mock_extract_cost.return_value = 0.05

        payload = InterviewChatRequestSchema(search_query_id=1, query="hello")
        res = await run_interview("session_abc", payload)

        assert res.interview_finished is True
        assert res.response == "Hello Candidate!"
        mock_agent.assert_called_once()
        mock_persist.assert_called_once_with(
            session_id="session_abc",
            user_message="hello",
            response_text="Hello Candidate!",
            request_cost=0.05,
            search_query_id=1,
            interview_finished=True,
        )

    @patch("src.jobs.pipelines.chat.iter_interview_events")
    def test_stream_interview(self, mock_iter: MagicMock) -> None:
        """
        Verify stream_interview returns a FastAPI StreamingResponse.

        Parameters
        ----------
        mock_iter : MagicMock
            Mock iter_interview_events.

        Returns
        -------
        None
        """
        mock_iter.return_value = AsyncMock()
        payload = InterviewChatRequestSchema(search_query_id=1, query="stream me")
        res = stream_interview("session_abc", payload)
        assert isinstance(res, StreamingResponse)

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.persist_chat_and_cost")
    @patch("src.jobs.pipelines.chat.extract_request_cost")
    @patch("src.jobs.pipelines.chat.dspy.streamify")
    @patch("src.jobs.pipelines.chat.build_request_payload")
    @patch("src.jobs.pipelines.chat.InterviewAgent")
    @patch("src.jobs.pipelines.chat.dspy.LM")
    async def test_iter_interview_events_success(
        self,
        mock_lm_cls: MagicMock,
        mock_agent_cls: MagicMock,
        mock_build_payload: AsyncMock,
        mock_streamify: MagicMock,
        mock_extract_cost: MagicMock,
        mock_persist: AsyncMock,
    ) -> None:
        """
        Verify iter_interview_events handles streaming chunks and completion events.

        Parameters
        ----------
        mock_lm_cls : MagicMock
            Mock DSPy LM.
        mock_agent_cls : MagicMock
            Mock InterviewAgent class.
        mock_build_payload : AsyncMock
            Mock build_request_payload.
        mock_streamify : MagicMock
            Mock dspy.streamify.
        mock_extract_cost : MagicMock
            Mock extract_request_cost.
        mock_persist : AsyncMock
            Mock persist_chat_and_cost.

        Returns
        -------
        None
        """
        mock_build_payload.return_value = MagicMock(
            job_title="Dev",
            unified_requirements="Reqs",
            chat_history=[],
            query="stream me",
        )
        mock_lm = MagicMock()
        mock_lm_cls.return_value = mock_lm
        mock_extract_cost.return_value = 0.02

        # Simulate streaming chunk objects
        chunk1 = MagicMock(spec=dspy.streaming.StreamResponse)
        chunk1.chunk = "Let me think."
        chunk1.signature_field_name = "reasoning"

        chunk2 = MagicMock(spec=dspy.streaming.StreamResponse)
        chunk2.chunk = "My answer."
        chunk2.signature_field_name = "response"

        chunk3 = MagicMock(spec=dspy.Prediction)
        chunk3.interview_finished = False
        chunk3.response = "My answer."

        async def mock_stream_agent(*args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
            yield chunk1
            yield chunk2
            yield chunk3

        mock_streamify.return_value = mock_stream_agent

        payload = InterviewChatRequestSchema(search_query_id=1, query="stream me")

        events = []
        async for event in iter_interview_events("session_abc", payload):
            events.append(event)

        assert len(events) == 3
        assert events[0]["type"] == "reasoning"
        assert events[0]["data"]["token"] == "Let me think."
        assert events[1]["type"] == "answer"
        assert events[1]["data"]["token"] == "My answer."
        assert events[2]["type"] == "complete"
        assert events[2]["data"]["response"] == "My answer."

        mock_persist.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.jobs.pipelines.chat.build_request_payload")
    async def test_iter_interview_events_error(
        self,
        mock_build_payload: AsyncMock,
    ) -> None:
        """
        Verify iter_interview_events yields error event on exception.

        Parameters
        ----------
        mock_build_payload : AsyncMock
            Mock build_request_payload.

        Returns
        -------
        None
        """
        mock_build_payload.side_effect = Exception("General error")
        payload = InterviewChatRequestSchema(search_query_id=1, query="stream me")

        events = []
        async for event in iter_interview_events("session_abc", payload):
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert events[0]["status"] == "error"
        assert "Internal server error" in events[0]["data"]["error"]
