"""
Unit tests for conversation history utilities in src/conversation_history/utils.py.

Verifies that the message conversion functions properly map back and forth
between LangChain message objects, simple dictionaries, and DSPy-compatible
representations.
"""

# Standart library imports
import ast
import json
from typing import List
from unittest.mock import MagicMock

# Thirdparty imports
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

# Local imports
from src.conversation_history.utils import (
    dict_to_dspy_format,
    dict_to_langchain,
    dicts_to_langchain_messages,
    langchain_messages_to_dicts,
    langchain_to_dict,
    tool_messages_from_flat_json,
)


class TestMessageConversions:
    """Test suite for LangChain message and dictionary conversion functions."""

    def test_langchain_to_dict(self) -> None:
        """
        Verify conversion of various LangChain message types to dictionary format.

        Returns
        -------
        None
        """
        human_msg = HumanMessage(content="Hello assistant")
        ai_msg = AIMessage(content="Hello human")
        tool_msg = ToolMessage(content="Tool result", tool_call_id="call_123")

        assert langchain_to_dict(human_msg) == {"role": "user", "content": "Hello assistant"}
        assert langchain_to_dict(ai_msg) == {"role": "assistant", "content": "Hello human"}
        assert langchain_to_dict(tool_msg) == {"role": "tool", "content": "Tool result"}

        # Unknown message type defaults to user
        unknown_msg = MagicMock(spec=BaseMessage)
        unknown_msg.content = "Unknown"
        assert langchain_to_dict(unknown_msg) == {"role": "user", "content": "Unknown"}

    def test_dict_to_langchain(self) -> None:
        """
        Verify conversion of role dictionaries to corresponding LangChain messages.

        Returns
        -------
        None
        """
        user_dict = {"role": "user", "content": "Hello"}
        assistant_dict = {"role": "assistant", "content": "Hi"}
        tool_dict = {"role": "tool", "content": "Success"}
        unknown_dict = {"role": "system", "content": "Init"}

        user_msg = dict_to_langchain(user_dict)
        assert isinstance(user_msg, HumanMessage)
        assert user_msg.content == "Hello"

        ai_msg = dict_to_langchain(assistant_dict)
        assert isinstance(ai_msg, AIMessage)
        assert ai_msg.content == "Hi"

        tool_msg = dict_to_langchain(tool_dict)
        assert isinstance(tool_msg, ToolMessage)
        assert tool_msg.content == "Success"
        assert tool_msg.tool_call_id == ""

        sys_msg = dict_to_langchain(unknown_dict)
        assert isinstance(sys_msg, HumanMessage)
        assert sys_msg.content == "Init"

    def test_list_conversions(self) -> None:
        """
        Verify batch conversion of messages and dictionaries.

        Returns
        -------
        None
        """
        messages: List[BaseMessage] = [
            HumanMessage(content="Query"),
            AIMessage(content="Response"),
            ToolMessage(content="Result", tool_call_id="1"),
        ]

        dicts = langchain_messages_to_dicts(messages)
        assert len(dicts) == 3
        assert dicts[0] == {"role": "user", "content": "Query"}
        assert dicts[2] == {"role": "tool", "content": "Result"}

        filtered_dicts = langchain_messages_to_dicts(messages, filter_tool_calls=True)
        assert len(filtered_dicts) == 2
        assert filtered_dicts[0]["role"] == "user"
        assert filtered_dicts[1]["role"] == "assistant"

        back_messages = dicts_to_langchain_messages(dicts)
        assert len(back_messages) == 3
        assert isinstance(back_messages[0], HumanMessage)
        assert isinstance(back_messages[1], AIMessage)
        assert isinstance(back_messages[2], ToolMessage)

    def test_dict_to_dspy_format(self) -> None:
        """
        Verify formatting of raw message dictionaries into DSPy expected formats.

        Returns
        -------
        None
        """
        raw_dicts = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "system", "content": "Ignored"},
            {"role": "user", "content": ""},  # Empty content should be ignored
            {"role": "tool", "content": "Data"},
        ]

        dspy_format = dict_to_dspy_format(raw_dicts)
        assert len(dspy_format) == 3
        assert dspy_format[0] == {"role": "user", "content": "Hello"}
        assert dspy_format[1] == {"role": "assistant", "content": "Hi"}
        assert dspy_format[2] == {"role": "tool", "content": "Data"}


class TestToolMessagesFromFlatJson:
    """Test suite for parsing flat JSON formats into ToolMessages."""

    def test_parse_flat_json_dict(self) -> None:
        """
        Verify tool message extraction from flat JSON dictionary structure.

        Returns
        -------
        None
        """
        flat_data = {
            "thought_1": "Let's lookup python vacancies",
            "tool_name_1": "search_jobs",
            "tool_args_1": '{"query": "python"}',
            "observation_1": '[{"id": 1, "title": "Python Dev"}]',
            "thought_2": "Let's finish",
            "tool_name_2": "finish",
            "tool_args_2": "{}",
            "observation_2": "Done",
        }

        tool_messages = tool_messages_from_flat_json(flat_data)
        # Should skip finish tool call (index 2), so only index 1 message remains
        assert len(tool_messages) == 1
        msg = tool_messages[0]
        assert isinstance(msg, ToolMessage)
        assert msg.name == "search_jobs"
        assert msg.tool_call_id == "tool_call_1"

        assert isinstance(msg.content, str)
        content = ast.literal_eval(msg.content)
        assert isinstance(content, dict)
        assert content["thought"] == "Let's lookup python vacancies"
        assert content["tool_name"] == "search_jobs"
        assert content["tool_args"] == {"query": "python"}
        assert content["observation"] == [{"id": 1, "title": "Python Dev"}]
        assert content["index"] == 1

    def test_parse_flat_json_string(self) -> None:
        """
        Verify tool message extraction from flat JSON serialized string.

        Returns
        -------
        None
        """
        flat_data_str = json.dumps(
            {
                "thought_1": "Call some tool",
                "tool_name_1": "some_tool",
                "tool_args_1": "plain_string_args",
                "observation_1": "plain_observation",
            }
        )

        tool_messages = tool_messages_from_flat_json(flat_data_str)
        assert len(tool_messages) == 1
        msg = tool_messages[0]
        assert msg.name == "some_tool"
        assert isinstance(msg.content, str)
        content = ast.literal_eval(msg.content)
        assert isinstance(content, dict)
        assert content["tool_args"] == "plain_string_args"
        assert content["observation"] == "plain_observation"

    def test_parse_empty_or_no_indices(self) -> None:
        """
        Verify tool message extraction on empty data returns an empty list.

        Returns
        -------
        None
        """
        assert tool_messages_from_flat_json({}) == []
        assert tool_messages_from_flat_json('{"key": "value"}') == []
