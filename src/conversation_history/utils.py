"""Utility functions for message format conversion."""

# Standart library imports
import json
from typing import Any, Dict, List, Union

# Thirdparty imports
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


def langchain_to_dict(message: BaseMessage) -> Dict[str, str]:
    """
    Convert a LangChain message to a dictionary format.

    Parameters
    ----------
    message : BaseMessage
        LangChain message object (HumanMessage, AIMessage, or ToolMessage).

    Returns
    -------
    Dict[str, str]
        Dictionary with 'role' and 'content' keys.
        Format: {"role": "user"|"assistant"|"tool", "content": "..."}

    Examples
    --------
    >>> msg = HumanMessage(content="Hello")
    >>> dict_to_dspy_format([langchain_to_dict(msg)])
    """
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, ToolMessage):
        role = "tool"
    else:
        # Default to user for unknown types
        role = "user"

    content = message.content if hasattr(message, "content") else str(message)
    return {"role": role, "content": content}


def dict_to_langchain(message_dict: Dict[str, str]) -> BaseMessage:
    """
    Convert a dictionary to a LangChain message object.

    Parameters
    ----------
    message_dict : Dict[str, str]
        Dictionary with 'role' and 'content' keys.

    Returns
    -------
    BaseMessage
        LangChain message object (HumanMessage, AIMessage, or ToolMessage).

    Examples
    --------
    >>> msg_dict = {"role": "user", "content": "Hello"}
    >>> msg = dict_to_langchain(msg_dict)
    """
    role = message_dict.get("role", "user")
    content = message_dict.get("content", "")

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
    elif role == "tool":
        return ToolMessage(content=content, tool_call_id="")
    else:
        # Default to user message
        return HumanMessage(content=content)


def langchain_messages_to_dicts(messages: List[BaseMessage], filter_tool_calls: bool = False) -> List[Dict[str, str]]:
    """
    Convert a list of LangChain messages to dictionaries.

    Parameters
    ----------
    messages : List[BaseMessage]
        List of LangChain message objects.

    Returns
    -------
    List[Dict[str, str]]
        List of message dictionaries with 'role' and 'content' keys.
    """
    result = []
    for msg in messages:
        if filter_tool_calls and isinstance(msg, ToolMessage):
            continue
        result.append(langchain_to_dict(msg))
    return result


def dicts_to_langchain_messages(messages: List[Dict[str, str]]) -> List[BaseMessage]:
    """
    Convert a list of dictionaries to LangChain messages.

    Parameters
    ----------
    messages : List[Dict[str, str]]
        List of message dictionaries with 'role' and 'content' keys.

    Returns
    -------
    List[BaseMessage]
        List of LangChain message objects.
    """
    return [dict_to_langchain(msg) for msg in messages]


def dict_to_dspy_format(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Convert simple message dicts to DSPy-compatible format.

    Parameters
    ----------
    messages : List[Dict[str, str]]
        List of message dictionaries with 'role' and 'content' keys.
        Format: [{"role": "user"|"assistant"|"tool", "content": "..."}, ...]

    Returns
    -------
    List[Dict[str, str]]
        List of DSPy-compatible message dictionaries.
        Format compatible with MessageLikeRepresentation.

    Examples
    --------
    >>> messages = [
    ...     {"role": "user", "content": "Hello"},
    ...     {"role": "assistant", "content": "Hi there!"}
    ... ]
    >>> dspy_format = dict_to_dspy_format(messages)
    """
    # DSPy expects messages in a format compatible with MessageLikeRepresentation
    # Include all three roles: user, assistant, and tool
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
        if msg.get("role") in ("user", "assistant", "tool") and msg.get("content")
    ]


def tool_messages_from_flat_json(data: Union[str, Dict[str, Any]]) -> List[ToolMessage]:
    """
    Convert a flat numbered JSON to a list of ToolMessages.

    Parameters
    ----------
    data : Union[str, Dict[str, Any]]
        The data to convert to a list of ToolMessages.

    Returns
    -------
    List[ToolMessage]
        The list of ToolMessages.
    """
    if isinstance(data, str):
        data = json.loads(data)

    # Collect all numeric suffixes
    indices = set()
    for k in data.keys():
        if "_" in k and k.rsplit("_", 1)[-1].isdigit():
            indices.add(int(k.rsplit("_", 1)[-1]))
    if not indices:
        return []

    messages: List[ToolMessage] = []
    for i in sorted(indices):
        thought = data.get(f"thought_{i}")
        tool_name = data.get(f"tool_name_{i}")
        tool_args = data.get(f"tool_args_{i}")
        observation = data.get(f"observation_{i}")

        # Skip finish tool calls
        if tool_name is not None and str(tool_name).strip().lower() == "finish":
            continue

        # Normalize args/obs types
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except Exception:
                pass
        if isinstance(observation, str):
            # If observation looks like JSON, parse; otherwise keep as plain text
            obs_parsed = None
            try:
                obs_parsed = json.loads(observation)
            except Exception:
                pass
        else:
            obs_parsed = observation

        # Pack content for ToolMessage; you can adjust fields to your needs
        content = {
            "thought": thought,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "observation": obs_parsed if obs_parsed is not None else observation,
            "index": i,
        }

        # ToolMessage typically requires a tool_call_id; generate a stable one per index
        tool_call_id = f"tool_call_{i}"
        messages.append(ToolMessage(content=content, name=tool_name, tool_call_id=tool_call_id))

    return messages
