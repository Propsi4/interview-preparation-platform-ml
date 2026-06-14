"""
Unit tests for the application configuration settings.

Verifies that the default configurations for the application are correctly
defined and loaded.
"""

# Local imports
from src.config.app import AppConfig, app_config


class TestAppConfig:
    """Test suite for the application configuration settings."""

    def test_app_config_defaults(self) -> None:
        """
        Verify that AppConfig has the expected default attributes and values.

        Returns
        -------
        None
        """
        assert isinstance(app_config, AppConfig)
        assert app_config.MAX_CHAT_HISTORY_LEN == 8
