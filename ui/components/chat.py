"""Chat rendering helpers."""

# Standart library imports
from typing import Any, Dict

# Thirdparty imports
import streamlit as st


def render_message(message: Dict[str, Any]) -> None:
    """
    Render a single chat message.

    Parameters
    ----------
    message : Dict[str, Any]
        Message payload with role and content.

    Returns
    -------
    None
        Writes message to the UI.
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    with st.chat_message(role):
        st.markdown(content)
