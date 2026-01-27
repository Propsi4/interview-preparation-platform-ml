"""State management utilities for the Streamlit UI."""

# Standart library imports
import uuid
from typing import Any, Dict, List, Optional

# Thirdparty imports
import streamlit as st


def init_session_state() -> None:
    """
    Initialize default session state values.

    Returns
    -------
    None
        Initializes Streamlit session state.
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "search_query_id" not in st.session_state:
        st.session_state.search_query_id = None
    if "interview_finished" not in st.session_state:
        st.session_state.interview_finished = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "progress" not in st.session_state:
        st.session_state.progress = {}
    if "last_loaded_session" not in st.session_state:
        st.session_state.last_loaded_session = None
    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = None
    if "search_queries" not in st.session_state:
        st.session_state.search_queries = []


def get_session_id() -> str:
    """
    Get the current session ID.

    Returns
    -------
    str
        Current session identifier.
    """
    if "session_id" not in st.session_state:
        init_session_state()
    return str(st.session_state.session_id)


def set_session_id(session_id: str) -> None:
    """
    Set the current session ID and clear session-bound state.

    Parameters
    ----------
    session_id : str
        New session identifier.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.session_id = session_id
    st.session_state.search_query_id = None
    st.session_state.interview_finished = False
    st.session_state.messages = []
    st.session_state.progress = {}
    st.session_state.last_loaded_session = None
    st.session_state.evaluation_results = None
    st.session_state.search_queries = []


def get_search_query_id() -> Optional[int]:
    """
    Get the active search query ID.

    Returns
    -------
    Optional[int]
        Search query identifier if set.
    """
    return st.session_state.get("search_query_id")


def set_search_query_id(search_query_id: Optional[int]) -> None:
    """
    Set the active search query ID.

    Parameters
    ----------
    search_query_id : Optional[int]
        Search query identifier.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.search_query_id = search_query_id


def get_search_queries() -> List[Dict[str, Any]]:
    """
    Get cached search queries.

    Returns
    -------
    List[Dict[str, Any]]
        Search query entries with id and query text.
    """
    return list(st.session_state.get("search_queries", []))


def add_search_query(search_query_id: int, search_query: str) -> None:
    """
    Add a search query entry to state.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.
    search_query : str
        Search query text.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    entries = st.session_state.get("search_queries", [])
    entries.append({"id": int(search_query_id), "query": search_query})
    st.session_state.search_queries = entries


def set_search_queries(entries: List[Dict[str, Any]]) -> None:
    """
    Replace cached search query entries.

    Parameters
    ----------
    entries : List[Dict[str, Any]]
        Search query entries with id and query.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.search_queries = list(entries)


def get_interview_finished() -> bool:
    """
    Get interview completion flag.

    Returns
    -------
    bool
        Interview completion state.
    """
    return bool(st.session_state.get("interview_finished", False))


def set_interview_finished(value: bool) -> None:
    """
    Set interview completion flag.

    Parameters
    ----------
    value : bool
        Interview completion state.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.interview_finished = bool(value)


def get_messages() -> List[Dict[str, Any]]:
    """
    Get cached chat messages.

    Returns
    -------
    List[Dict[str, Any]]
        Messages list.
    """
    return list(st.session_state.get("messages", []))


def set_messages(messages: List[Dict[str, Any]]) -> None:
    """
    Replace cached chat messages.

    Parameters
    ----------
    messages : List[Dict[str, Any]]
        Messages list.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.messages = list(messages)


def add_message(role: str, content: str) -> None:
    """
    Append a chat message to state.

    Parameters
    ----------
    role : str
        Message role.
    content : str
        Message content.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    messages = st.session_state.get("messages", [])
    messages.append({"role": role, "content": content})
    st.session_state.messages = messages


def get_progress() -> Dict[str, Any]:
    """
    Get cached progress payload.

    Returns
    -------
    Dict[str, Any]
        Progress payload.
    """
    return dict(st.session_state.get("progress", {}))


def set_progress(progress: Dict[str, Any]) -> None:
    """
    Update cached progress payload.

    Parameters
    ----------
    progress : Dict[str, Any]
        Progress payload.

    Returns
    -------
    None
        Updates Streamlit session state.
    """
    st.session_state.progress = dict(progress)
