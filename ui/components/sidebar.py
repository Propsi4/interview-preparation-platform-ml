"""Sidebar component for session management."""

# Standart library imports
import asyncio
import uuid
from typing import Any, Dict, List

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import InterviewAPIClient
from ui.config.settings import settings
from ui.utils.state import set_session_id


def _fetch_sessions(client: InterviewAPIClient) -> List[Dict[str, Any]]:
    """
    Fetch chat sessions from the API.

    Parameters
    ----------
    client : InterviewAPIClient
        API client.

    Returns
    -------
    List[Dict[str, Any]]
        Session list payload.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(client.list_sessions())
    finally:
        loop.close()


def render_sidebar() -> None:
    """
    Render the sidebar with session selection.

    Returns
    -------
    None
        Writes sidebar elements.
    """
    with st.sidebar:
        st.title(f"{settings.PAGE_ICON} {settings.PAGE_TITLE}")
        st.divider()

        st.subheader("Session Management")

        client = InterviewAPIClient()
        sessions: List[Dict[str, Any]] = []
        try:
            sessions = _fetch_sessions(client)
        except Exception as exc:
            st.warning(f"Could not load sessions: {exc}")

        NEW_SESSION_MARKER = "new_session_marker"
        options = [NEW_SESSION_MARKER] + [session["session_id"] for session in sessions]
        current_session_id = st.session_state.get("session_id", str(uuid.uuid4()))

        index = 0
        if current_session_id in options:
            index = options.index(current_session_id)

        if st.session_state.get("new_session_pending") and current_session_id in options:
            st.session_state.sidebar_session_selector = current_session_id
            st.session_state.new_session_pending = False

        def format_option(option: str) -> str:
            if option == NEW_SESSION_MARKER:
                return "➕ New Session"
            session = next((item for item in sessions if item["session_id"] == option), None)
            if session:
                title = session.get("title") or "Untitled"
                if len(title) > 30:
                    title = title[:27] + "..."
                status = "✅" if session.get("interview_finished") else "🟡"
                return f"{status} {title}"
            return option

        selected_option = st.selectbox(
            "Select Session",
            options=options,
            format_func=format_option,
            index=index,
            key="sidebar_session_selector",
        )
        previous_selection = st.session_state.get("sidebar_session_selector_prev")
        st.session_state.sidebar_session_selector_prev = selected_option

        if selected_option == NEW_SESSION_MARKER:
            if previous_selection != NEW_SESSION_MARKER:
                new_id = str(uuid.uuid4())
                st.session_state.new_session_pending = True
                set_session_id(new_id)
                st.rerun()
        else:
            if selected_option != current_session_id:
                set_session_id(selected_option)
                st.rerun()

        st.caption(f"ID: `{current_session_id}`")
        st.divider()
        st.caption("Version: 1.0.0")
