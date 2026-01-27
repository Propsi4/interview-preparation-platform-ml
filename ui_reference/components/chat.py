"""Chat component for rendering messages."""

# Standart library imports
import base64
from typing import Any, Dict

# Thirdparty imports
import streamlit as st


def render_message(message: Dict[str, Any]):
    """
    Render a single chat message.

    Parameters
    ----------
    message : Dict[str, Any]
        The message dictionary containing 'role', 'content', and optional 'attachments'.
    """
    role = message.get("role", "user")
    content = message.get("content", "")
    attachments = message.get("attachments", [])

    with st.chat_message(role):
        st.markdown(content)

        if attachments:
            st.markdown("---")
            st.caption("Attachments:")
            for i, attachment in enumerate(attachments):
                file_content = attachment.get("file_content")
                file_type = attachment.get("file_type", "file")

                if file_content:
                    data = None
                    # Attempt to handle content as base64 if it's a string and looks like binary might be expected (e.g. docx)
                    # Or just try to decode and if fail assume text.
                    if isinstance(file_content, str):
                        try:
                            data = base64.b64decode(file_content)
                        except Exception:
                            # If decode fails, it might be plain text
                            data = file_content.encode("utf-8")
                    elif isinstance(file_content, bytes):
                        data = file_content

                    if data:
                        st.download_button(
                            label=f"Download Attachment {i+1} ({file_type})",
                            data=data,
                            file_name=f"attachment_{i+1}.{file_type}",
                            mime="application/octet-stream",
                            key=f"download_{i}_{hash(content)}",
                        )
