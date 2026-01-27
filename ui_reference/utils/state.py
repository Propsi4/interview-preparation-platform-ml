"""State management utilities for the UI."""

# Standart library imports
import uuid
from typing import Any, Dict, List, Optional

# Thirdparty imports
import streamlit as st


def init_session_state():
    """Initialize the session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_price" not in st.session_state:
        st.session_state.session_price = 0.0


def get_session_id() -> str:
    """
    Get the current session ID.

    Returns
    -------
    str
        The session ID.
    """
    if "session_id" not in st.session_state:
        init_session_state()
    return st.session_state.session_id


def set_session_id(session_id: str):
    """
    Set the current session ID.

    Parameters
    ----------
    session_id : str
        The new session ID.
    """
    st.session_state.session_id = session_id
    # Clear messages when switching sessions to force a refresh
    st.session_state.messages = []
    st.session_state.session_price = 0.0


def get_session_price() -> float:
    """
    Get the current session price from state.

    Reads the price tracked for the active chat session from Streamlit state.

    Returns
    -------
    float
        The stored session price.

    Examples
    --------
    >>> price = get_session_price()
    """
    if "session_price" not in st.session_state:
        st.session_state.session_price = 0.0
    return float(st.session_state.session_price)


def set_session_price(price: float) -> None:
    """
    Set the current session price in state.

    Updates Streamlit state with a new total for the active session.

    Parameters
    ----------
    price : float
        The session price to store.

    Returns
    -------
    None
        This function updates ``st.session_state`` in place.

    Examples
    --------
    >>> set_session_price(0.02)
    """
    st.session_state.session_price = float(price)


def add_message(role: str, content: str, attachments: Optional[List[Dict[str, Any]]] = None):
    """
    Add a message to the chat history.

    Parameters
    ----------
    role : str
        The sender role ('user' or 'assistant').
    content : str
        The message content.
    attachments : Optional[List[Dict[str, Any]]]
        Optional list of attachments to associate with the message.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    message: Dict[str, Any] = {"role": role, "content": content}
    if attachments:
        message["attachments"] = attachments
    st.session_state.messages.append(message)


def get_messages() -> List[Dict[str, Any]]:
    """
    Get the chat history.

    Returns
    -------
    List[Dict[str, Any]]
        List of messages.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    return st.session_state.messages


def set_messages(messages: List[Dict[str, Any]]):
    """
    Replace the stored chat history.

    Parameters
    ----------
    messages : List[Dict[str, Any]]
        List of message dictionaries to store in session state.

    Returns
    -------
    None
        This function updates ``st.session_state`` in place.
    """
    st.session_state.messages = list(messages)
