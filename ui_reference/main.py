"""Main entry point for the UI."""

# Standart library imports
import sys

# Thirdparty imports
import streamlit as st
from streamlit import Page
from streamlit.web import cli as stcli


def main():
    """Run the Streamlit UI."""
    nav = st.navigation(
        [
            Page(page="pages/home.py", title="Home", icon="🏠", default=True),
            Page(page="pages/chat.py", title="Chat", icon="✨"),
            Page(page="pages/history.py", title="History", icon="📜"),
        ]
    )
    nav.run()


def run_ui():
    """Entry point for poetry script."""
    sys.argv = ["streamlit", "run", "ui/main.py"]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
