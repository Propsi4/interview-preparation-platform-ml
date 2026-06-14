"""
Unit tests for the logging configuration.

Verifies that the logging configuration module loads properly and
that the logger object can record messages successfully.
"""

# Standart library imports
import os

# Thirdparty imports
import pytest

# Local imports
from src.core.logging import logger


class TestLogging:
    """Test suite for the logging configuration."""

    def test_logger_initialization(self) -> None:
        """
        Verify that the logger is initialized and log directory exists.

        Returns
        -------
        None
        """
        # Ensure log directory was created (relative path from codebase/ml)
        expected_log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
        normalized_path = os.path.abspath(expected_log_dir)
        assert os.path.exists(normalized_path)

    def test_logger_write(self) -> None:
        """
        Verify that the logger can write log statements without raising exceptions.

        Returns
        -------
        None
        """
        try:
            logger.info("Test log entry from unit tests.")
        except Exception as e:
            pytest.fail(f"Logger failed to write message: {e}")
