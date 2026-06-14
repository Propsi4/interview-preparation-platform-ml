"""
Unit tests for the ConversationHistoryManager class.

Verifies message retrieval, session summary details, pricing increments,
status updates, title changes, session deletions, and database health check queries.
"""

# Standart library imports
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from langchain_core.messages import BaseMessage, HumanMessage

# Local imports
from src.conversation_history.manager import ConversationHistoryManager
from src.conversation_history.schemas import ChatMessageSchema, ChatSessionOverviewSchema


class TestConversationHistoryManager:
    """Test suite for the ConversationHistoryManager class."""

    @pytest.mark.asyncio
    async def test_get_messages_for_session(self, mock_db_connection: MagicMock) -> None:
        """
        Verify retrieval and conversion of chat messages for a session.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        # Create mock message objects returned by repository
        msg1 = MagicMock()
        msg1.id = 1
        msg1.role = "user"
        msg1.content = "Hello"
        msg2 = MagicMock()
        msg2.id = 2
        msg2.role = "assistant"
        msg2.content = "Hi"

        with patch("src.conversation_history.manager.ChatMessageRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.list_by_session_id = AsyncMock(return_value=[msg2, msg1])  # Unsorted

            messages = await manager.get_messages_for_session("session_abc")

            assert len(messages) == 2
            # Verify sorting by ID
            assert messages[0].content == "Hello"  # ID 1
            assert messages[1].content == "Hi"  # ID 2
            mock_repo.list_by_session_id.assert_called_once_with("session_abc")

    @pytest.mark.asyncio
    async def test_get_session_history_with_ids(self, mock_db_connection: MagicMock) -> None:
        """
        Verify retrieving session messages returning ChatMessageSchema list.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        msg = MagicMock()
        msg.id = 10
        msg.role = "user"
        msg.content = "Help"
        msg.created_at = datetime(2026, 6, 8, 12, 0, 0)

        with patch("src.conversation_history.manager.ChatMessageRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.list_by_session_id = AsyncMock(return_value=[msg])

            schemas = await manager.get_session_history_with_ids("session_abc", filter_tool_calls=True)

            assert len(schemas) == 1
            assert isinstance(schemas[0], ChatMessageSchema)
            assert schemas[0].id == 10
            assert schemas[0].role == "user"
            assert schemas[0].content == "Help"

    @pytest.mark.asyncio
    async def test_get_all_sessions(self, mock_db_connection: MagicMock) -> None:
        """
        Verify retrieving all chat sessions overview lists.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()
        sess.session_id = "session_123"
        sess.title = "Vacancy Interview"
        sess.created_at = datetime(2026, 6, 8, 10, 0, 0)
        sess.updated_at = datetime(2026, 6, 8, 11, 0, 0)
        sess.price = 0.05
        sess.interview_finished = False
        sess.evaluated = True
        sess.search_query_id = 99

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_sess_repo_cls, patch(
            "src.conversation_history.manager.ChatMessageRepository"
        ) as mock_msg_repo_cls:

            mock_sess_repo = mock_sess_repo_cls.return_value
            mock_sess_repo.list_all = AsyncMock(return_value=[sess])

            mock_msg_repo = mock_msg_repo_cls.return_value
            mock_msg_repo.count_by_session_id = AsyncMock(return_value=15)

            sessions = await manager.get_all_sessions()

            assert len(sessions) == 1
            assert isinstance(sessions[0], ChatSessionOverviewSchema)
            assert sessions[0].session_id == "session_123"
            assert sessions[0].total_messages == 15

    @pytest.mark.asyncio
    async def test_get_session_price(self, mock_db_connection: MagicMock) -> None:
        """
        Verify retrieving current session accumulated cost.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()
        sess.price = 0.123

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_session_id = AsyncMock(return_value=sess)

            price = await manager.get_session_price("session_123")
            assert price == 0.123

            # Test session not found
            mock_repo.get_by_session_id = AsyncMock(return_value=None)
            assert await manager.get_session_price("session_unknown") == 0.0

    @pytest.mark.asyncio
    async def test_increment_session_price(self, mock_db_connection: MagicMock) -> None:
        """
        Verify pricing increment updates existing session cost.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()
        sess.price = 0.10

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_session_id = AsyncMock(return_value=sess)
            mock_repo.commit = AsyncMock()

            new_price = await manager.increment_session_price("session_123", 0.05)
            assert sess.price == pytest.approx(0.15)
            assert new_price == pytest.approx(0.15)
            mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_interview_finished(self, mock_db_connection: MagicMock) -> None:
        """
        Verify updating finish status flag on the session.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()
        sess.interview_finished = False

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_session_id = AsyncMock(return_value=sess)
            mock_repo.commit = AsyncMock()

            await manager.set_interview_finished("session_123", True)
            assert sess.interview_finished is True
            mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_messages(self, mock_db_connection: MagicMock) -> None:
        """
        Verify persisting message list and creating session model if missing.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_sess_repo_cls, patch(
            "src.conversation_history.manager.ChatMessageRepository"
        ) as mock_msg_repo_cls:

            mock_sess_repo = mock_sess_repo_cls.return_value
            mock_sess_repo.get_by_session_id = AsyncMock(return_value=None)  # Session does not exist yet
            mock_sess_repo.add = AsyncMock()
            mock_sess_repo.commit = AsyncMock()

            mock_msg_repo = mock_msg_repo_cls.return_value
            mock_msg_repo.add_all = AsyncMock()

            messages: list[BaseMessage] = [HumanMessage(content="Hello assistant")]
            await manager.save_messages("session_123", 99, messages)

            # Assert session added
            mock_sess_repo.add.assert_called_once()
            # Assert message added
            mock_msg_repo.add_all.assert_called_once()
            # Commit called
            mock_sess_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_session_title(self, mock_db_connection: MagicMock) -> None:
        """
        Verify updating session title by ID.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()
        sess.title = "Old Title"

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_session_id = AsyncMock(return_value=sess)
            mock_repo.commit = AsyncMock()

            success = await manager.update_session_title("session_123", "New Title")
            assert success is True
            assert sess.title == "New Title"

    @pytest.mark.asyncio
    async def test_delete_chat_by_session_id(self, mock_db_connection: MagicMock) -> None:
        """
        Verify deleting session by ID.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        sess = MagicMock()

        with patch("src.conversation_history.manager.ChatSessionRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.get_by_session_id = AsyncMock(return_value=sess)
            mock_repo.delete = AsyncMock()
            mock_repo.commit = AsyncMock()

            success = await manager.delete_chat_by_session_id("session_123")
            assert success is True
            mock_repo.delete.assert_called_once_with(sess)

    @pytest.mark.asyncio
    async def test_check_health(self, mock_db_connection: MagicMock) -> None:
        """
        Verify health check execution status.

        Parameters
        ----------
        mock_db_connection : MagicMock
            Mock database connection fixture.

        Returns
        -------
        None
        """
        manager = ConversationHistoryManager()

        # Database returns 1
        mock_db_connection.execute.return_value.scalar_one = MagicMock(return_value=1)
        assert await manager.check_health() is True

        # Database throws exception
        mock_db_connection.execute.side_effect = Exception("DB error")
        assert await manager.check_health() is False
