"""Main entry point for the Streamlit UI."""

# Standart library imports
import sys

# Thirdparty imports
import streamlit as st
from streamlit import Page
from streamlit.web import cli as stcli


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


def run_ui() -> None:
    """
    Entry point for running the UI via a script.

    Returns
    -------
    None
        Executes Streamlit CLI.
    """
    sys.argv = ["streamlit", "run", "ui/main.py"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
