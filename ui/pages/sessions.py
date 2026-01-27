"""Session management page."""

# Standart library imports
import asyncio
import uuid
from typing import Any, Dict, List

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import InterviewAPIClient
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import get_session_id, init_session_state, set_session_id

st.set_page_config(page_title=f"Sessions - {settings.PAGE_TITLE}", page_icon="🗂️", layout=settings.LAYOUT)

init_session_state()
render_sidebar()

client = InterviewAPIClient()

st.title("🗂️ Sessions")
st.caption(f"Current session: `{get_session_id()}`")


def _run_async(coro) -> Any:
    """
    Run an async coroutine in a dedicated event loop.

    Parameters
    ----------
    coro : Any
        Coroutine to execute.

    Returns
    -------
    Any
        Coroutine result.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


try:
    sessions: List[Dict[str, Any]] = _run_async(client.list_sessions())
except Exception as exc:
    st.error(f"Failed to load sessions: {exc}")
    sessions = []

if not sessions:
    st.info("No sessions found.")
    st.stop()

session_ids = [session["session_id"] for session in sessions]

session_table = [
    {
        "Session ID": session.get("session_id"),
        "Title": session.get("title"),
        "Messages": session.get("total_messages"),
        "Interview Finished": session.get("interview_finished"),
        "Updated": session.get("updated_at"),
    }
    for session in sessions
]
st.dataframe(session_table, width="content")

st.divider()
selected_session = st.selectbox("Select a session", options=session_ids)
selected_title = next((s.get("title", "") for s in sessions if s["session_id"] == selected_session), "")
new_title = st.text_input("Rename session", value=selected_title)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Switch to Session", key="switch_session"):
        set_session_id(selected_session)
        st.success(f"Switched to session {selected_session}")
        st.rerun()

with col2:
    if st.button("Rename Session", key="rename_session"):
        try:
            _run_async(client.rename_session(selected_session, new_title))
            st.success("Session renamed.")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to rename session: {exc}")

with col3:
    if st.button("Delete Session", key="delete_session"):
        try:
            _run_async(client.delete_session(selected_session))
            st.success("Session deleted.")
            if get_session_id() == selected_session:
                set_session_id(str(uuid.uuid4()))
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to delete session: {exc}")
