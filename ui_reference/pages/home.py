"""Main page implementation."""

# Thirdparty imports
import streamlit as st

# Local imports
from ui.components.sidebar import render_sidebar
from ui.config.settings import settings
from ui.utils.state import init_session_state

st.set_page_config(page_title=settings.PAGE_TITLE, page_icon=settings.PAGE_ICON, layout=settings.LAYOUT)

# Initialize state
init_session_state()

# Sidebar
render_sidebar()

# Main content
st.title(f"{settings.PAGE_ICON} Welcome to {settings.PAGE_TITLE}")

st.markdown(
    """
    This is the official interface for the **Project Estimation Tool**.

    ### Features

    - **💬 Chat**: Interact with the AI agent to generate proposals, manage projects, and communicate with the orchestrator.
    - **📜 History**: View and manage your chat sessions.

    ### Specialized Tools

    - **Insert Specialist Profile**: In the Chat interface, you can easily load specialist profiles to provide context to the agent.

    ### Getting Started

    Select a page from the sidebar to begin.
    """
)
