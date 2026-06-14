"""
Unit tests for the API configuration settings.

Verifies that the default configurations for API host, port, CORS settings,
and reload configurations are correctly defined and loaded.
"""

# Thirdparty imports
import pytest

# Local imports
from src.config.api import APIConfig


class TestAPIConfig:
    """Test suite for the API configuration settings."""

    def test_api_config_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Verify that APIConfig has the expected default attributes and values.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch utility.

        Returns
        -------
        None
        """
        monkeypatch.setenv("RELOAD_ON_CODE_CHANGE", "false")
        config = APIConfig()
        assert config.API_HOST == "0.0.0.0"
        assert config.API_PORT == 8080
        assert config.DEBUG is False
        assert config.RELOAD_ON_CODE_CHANGE is False
        assert config.CORS_ALLOWED_ORIGINS == ["*"]
