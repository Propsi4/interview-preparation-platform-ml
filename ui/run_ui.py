"""Main entry point for the Streamlit UI."""

# Standart library imports
import sys

# Thirdparty imports
from streamlit.web import cli as stcli

# Local imports
from ui.config.settings import settings


def run_ui() -> None:
    """
    Entry point for running the UI via a script.

    Returns
    -------
    None
        Executes Streamlit CLI.
    """
    sys.argv = [
        "streamlit",
        "run",
        "ui/main.py"
    ]
    if settings.HOST:
        sys.argv.append("--server.address")
        sys.argv.append(settings.HOST)
    if settings.PORT:
        sys.argv.append("--server.port")
        sys.argv.append(str(settings.PORT))
    sys.exit(stcli.main())


if __name__ == "__main__":
    run_ui()
