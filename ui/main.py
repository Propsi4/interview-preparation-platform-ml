"""Main entry point for the Streamlit UI."""

# Thirdparty imports
import streamlit as st
from streamlit import Page


def main() -> None:
    """
    Run the Streamlit UI.

    Returns
    -------
    None
        Starts Streamlit navigation.
    """
    nav = st.navigation(
        [
            Page(page="pages/home.py", title="Home", icon="🏠", default=True),
            Page(page="pages/chat.py", title="Chat", icon="💬"),
            Page(page="pages/sessions.py", title="Sessions", icon="🗂️"),
        ]
    )
    nav.run()


if __name__ == "__main__":
    main()
