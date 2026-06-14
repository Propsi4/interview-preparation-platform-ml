"""
Unit tests for shared utility functions in src/utils.py.

Verifies that the cost extraction utility correctly parses cost information from
DSPy language models and that the persistence helper correctly forwards calls to
the history manager.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest

# Local imports
from src.utils import extract_request_cost, persist_chat_and_cost


class TestExtractRequestCost:
    """Test suite for the extract_request_cost function."""

    def test_extract_cost_dict_history(self) -> None:
        """
        Verify cost extraction when the history items are dictionaries.

        Returns
        -------
        None
        """
        mock_lm = MagicMock()
        mock_lm.history = [
            {"cost": 0.0015},
            {"cost": "0.002"},
            {"cost": None},
            {"no_cost_key": 1.0},
            {"cost": "invalid_number"},
        ]

        # Extracting from start_index=0
        cost = extract_request_cost(mock_lm, start_index=0)
        assert cost == 0.0035

        # Extracting from start_index=2
        cost_subset = extract_request_cost(mock_lm, start_index=2)
        assert cost_subset == 0.0

    def test_extract_cost_object_history(self) -> None:
        """
        Verify cost extraction when the history items are objects.

        Returns
        -------
        None
        """
        mock_lm = MagicMock()
        item1 = MagicMock()
        item1.cost = 0.005
        item2 = MagicMock()
        item2.cost = 0.002
        item3 = MagicMock()
        del item3.cost  # No cost attribute

        mock_lm.history = [item1, item2, item3]

        cost = extract_request_cost(mock_lm, start_index=0)
        assert cost == 0.007

    def test_extract_cost_empty_history(self) -> None:
        """
        Verify cost extraction when history is empty or missing.

        Returns
        -------
        None
        """
        mock_lm_empty = MagicMock()
        mock_lm_empty.history = []
        assert extract_request_cost(mock_lm_empty, start_index=0) == 0.0

        mock_lm_none = MagicMock(spec=[])  # No history attribute
        assert extract_request_cost(mock_lm_none, start_index=0) == 0.0


class TestPersistChatAndCost:
    """Test suite for the persist_chat_and_cost asynchronous function."""

    @pytest.mark.asyncio
    async def test_persist_chat_and_cost_success(self) -> None:
        """
        Verify persist_chat_and_cost saves messages and updates cost and finish status.

        Returns
        -------
        None
        """
        with patch("src.utils.history_manager") as mock_manager:
            mock_manager.save_messages = AsyncMock()
            mock_manager.increment_session_price = AsyncMock()
            mock_manager.set_interview_finished = AsyncMock()

            await persist_chat_and_cost(
                session_id="session_123",
                search_query_id=456,
                user_message="Hello",
                response_text="Hi there",
                request_cost=0.002,
                interview_finished=True,
            )

            # Check save_messages call
            mock_manager.save_messages.assert_called_once()
            args, kwargs = mock_manager.save_messages.call_args
            assert kwargs["session_id"] == "session_123"
            assert kwargs["search_query_id"] == 456
            assert len(kwargs["messages"]) == 2
            assert kwargs["messages"][0].content == "Hello"
            assert kwargs["messages"][1].content == "Hi there"

            # Check cost increment and interview finished calls
            mock_manager.increment_session_price.assert_called_once_with("session_123", 0.002)
            mock_manager.set_interview_finished.assert_called_once_with("session_123", True)

    @pytest.mark.asyncio
    async def test_persist_chat_and_cost_no_cost_not_finished(self) -> None:
        """
        Verify that cost and finish updates are skipped when zero cost and finished=False/None.

        Returns
        -------
        None
        """
        with patch("src.utils.history_manager") as mock_manager:
            mock_manager.save_messages = AsyncMock()
            mock_manager.increment_session_price = AsyncMock()
            mock_manager.set_interview_finished = AsyncMock()

            await persist_chat_and_cost(
                session_id="session_123",
                search_query_id=456,
                user_message="Hello",
                response_text="Hi there",
                request_cost=0.0,
                interview_finished=None,
            )

            mock_manager.save_messages.assert_called_once()
            mock_manager.increment_session_price.assert_not_called()
            mock_manager.set_interview_finished.assert_not_called()
