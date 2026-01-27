"""Home page for the Streamlit UI."""

# Thirdparty imports
import streamlit as st

# Local imports
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import init_session_state

st.set_page_config(page_title=settings.PAGE_TITLE, page_icon=settings.PAGE_ICON, layout=settings.LAYOUT)

init_session_state()
render_sidebar()

st.title(f"{settings.PAGE_ICON} {settings.PAGE_TITLE}")
st.markdown(
    """
    Welcome to the Interview Preparation Platform UI.

    Use the navigation menu to:
    - Create and monitor search queries.
    - Chat with the interview agent.
    - Manage chat sessions and evaluation results.
    """
)
