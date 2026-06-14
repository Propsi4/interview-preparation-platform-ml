"""
Unit tests for the OpenAI configuration settings.

Verifies that the default configurations for the OpenAI API, models, and parameters
are correctly defined and loaded from the environment.
"""

# Thirdparty imports
import pytest

# Local imports
from src.config.openai import OpenAIConfig


class TestOpenAIConfig:
    """Test suite for the OpenAI configuration settings."""

    def test_openai_config_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Verify that OpenAIConfig has the expected default attributes and values.

        Parameters
        ----------
        monkeypatch : pytest.MonkeyPatch
            Pytest monkeypatch utility.

        Returns
        -------
        None
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-key-for-testing-purposes-only-12345")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.0")
        monkeypatch.setenv("LLM_MAX_TOKENS", "32000")
        config = OpenAIConfig(OPENAI_API_KEY="sk-mock-key-for-testing-purposes-only-12345")
        assert config.API_KEY == "sk-mock-key-for-testing-purposes-only-12345"
        assert config.EMBEDDING_MODEL == "text-embedding-3-small"
        assert config.EMBEDDING_DIMENSION == 1536
        assert config.LLM_MODEL == "openai/gpt-4.1-mini"
        assert config.LLM_TEMPERATURE == 0.0
        assert config.LLM_MAX_TOKENS == 32_000
        assert config.STT_MODEL == "whisper-1"
        assert config.TTS_MODEL == "gpt-4o-mini-tts"
        assert config.TTS_VOICE == "alloy"
        assert config.TTS_SPEED == 1.2
        assert config.TTS_OUTPUT_FORMAT == "mp3"
        assert config.ADDITIONAL_LLM_KWARGS == {}
