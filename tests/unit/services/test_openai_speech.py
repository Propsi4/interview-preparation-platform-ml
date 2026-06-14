"""
Unit tests for speech services in src/services/openai_speech.py.

Verifies that transcribe_audio correctly interacts with the OpenAI client
for speech-to-text processing and that stream_tts_audio correctly maps formats
and streams audio bytes using the client's speech synthesis.
"""

# Standart library imports
from unittest.mock import MagicMock, patch

# Thirdparty imports
import pytest

# Local imports
from src.services.openai_speech import _resolve_tts_format, stream_tts_audio, transcribe_audio


class TestOpenAISpeech:
    """Test suite for the OpenAI speech service functions."""

    def test_resolve_tts_format(self) -> None:
        """
        Verify correct mapping of various file format strings to OpenAI formats.

        Returns
        -------
        None
        """
        assert _resolve_tts_format(None) == "mp3"
        assert _resolve_tts_format("pcm_16") == "pcm"
        assert _resolve_tts_format("WAV") == "wav"
        assert _resolve_tts_format("ogg_opus") == "opus"
        assert _resolve_tts_format("flac") == "flac"
        assert _resolve_tts_format("aac") == "aac"
        assert _resolve_tts_format("unknown") == "mp3"

    def test_transcribe_audio(self) -> None:
        """
        Verify that transcribe_audio calls the OpenAI API and returns parsed text.

        Returns
        -------
        None
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a transcribed sentence."
        mock_client.audio.transcriptions.create.return_value = mock_response

        with patch("src.services.openai_speech.get_openai_client", return_value=mock_client):
            text = transcribe_audio(
                audio_bytes=b"dummy_audio_bytes",
                file_name="audio.wav",
                language_code="en",
            )

            assert text == "This is a transcribed sentence."
            mock_client.audio.transcriptions.create.assert_called_once()
            _, kwargs = mock_client.audio.transcriptions.create.call_args
            assert kwargs["language"] == "en"
            assert kwargs["file"].read() == b"dummy_audio_bytes"

    def test_transcribe_audio_empty_response_raises(self) -> None:
        """
        Verify that transcribe_audio raises ValueError if OpenAI response has no text.

        Returns
        -------
        None
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # Empty text
        mock_client.audio.transcriptions.create.return_value = mock_response

        with patch("src.services.openai_speech.get_openai_client", return_value=mock_client):
            with pytest.raises(ValueError, match="OpenAI transcription response missing text"):
                transcribe_audio(b"audio", "test.wav")

    def test_stream_tts_audio_iter_bytes(self) -> None:
        """
        Verify that stream_tts_audio yields audio chunks when iter_bytes is callable.

        Returns
        -------
        None
        """
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2", None]
        mock_client.audio.speech.create.return_value = mock_response

        with patch("src.services.openai_speech.get_openai_client", return_value=mock_client):
            chunks = list(stream_tts_audio("Hello world", voice_id="alloy", model_id="tts-1"))
            assert chunks == [b"chunk1", b"chunk2"]
            mock_client.audio.speech.create.assert_called_once()
            _, kwargs = mock_client.audio.speech.create.call_args
            assert kwargs["input"] == "Hello world"
            assert kwargs["voice"] == "alloy"
            assert kwargs["model"] == "tts-1"

    def test_stream_tts_audio_fallback_content(self) -> None:
        """
        Verify stream_tts_audio falls back to returning the full content if iter_bytes is missing.

        Returns
        -------
        None
        """
        mock_client = MagicMock()
        mock_response = MagicMock(spec=[])  # No iter_bytes method
        mock_response.content = b"full_synthesized_audio_data"
        mock_client.audio.speech.create.return_value = mock_response

        with patch("src.services.openai_speech.get_openai_client", return_value=mock_client):
            chunks = list(stream_tts_audio("Fallback text"))
            assert chunks == [b"full_synthesized_audio_data"]
