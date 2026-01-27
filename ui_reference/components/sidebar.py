"""Sidebar component for the UI."""

# Standart library imports
import asyncio
import uuid

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import PETClient
from ui.config.settings import settings
from ui.utils.state import set_session_id


def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        st.title(f"{settings.PAGE_ICON} {settings.PAGE_TITLE}")

        st.divider()

        st.subheader("Session Management")

        # Fetch conversations
        client = PETClient()
        conversations = []
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            conversations = loop.run_until_complete(client.list_conversations())
            loop.close()
        except Exception as e:
            st.warning(f"Could not load sessions: {e}")

        # Prepare options
        NEW_SESSION_MARKER = "new_session_marker"

        # Create options list: [MARKER] + [session_ids...]
        options = [NEW_SESSION_MARKER] + [c['session_id'] for c in conversations]

        # Determine current selection
        current_session_id = st.session_state.get("session_id", str(uuid.uuid4()))

        # Default index is 0 (New Session) unless current ID is in the list
        index = 0
        if current_session_id in options:
            index = options.index(current_session_id)

        def format_func(option):
            if option == NEW_SESSION_MARKER:
                return "➕ New Session"

            # Find conversation details
            conv = next((c for c in conversations if c['session_id'] == option), None)
            if conv:
                title = conv.get('title') or "Untitled"
                # Truncate long titles
                if len(title) > 30:
                    title = title[:27] + "..."
                return f"{title}"
            return option

        selected_option = st.selectbox(
            "Select Session", options=options, format_func=format_func, index=index, key="sidebar_session_selector"
        )

        # Handle selection logic
        if selected_option == NEW_SESSION_MARKER:
            # If we were in an existing session (in the list), and switched to New
            if current_session_id in [c['session_id'] for c in conversations]:
                new_id = str(uuid.uuid4())
                set_session_id(new_id)
                st.rerun()
            # If current_session_id is not in list (i.e. already a new/unsaved session),
            # we do nothing, keeping the current unsaved session.
        else:
            # Switched to an existing session
            if selected_option != current_session_id:
                set_session_id(selected_option)
                st.rerun()

        st.caption(f"ID: `{current_session_id}`")

        st.divider()

        st.caption("Version: 1.0.0")
