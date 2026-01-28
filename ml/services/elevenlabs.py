"""ElevenLabs speech services."""

# Standart library imports
from functools import lru_cache
from io import BytesIO
from typing import Iterable, Optional

# Thirdparty imports
from elevenlabs import ElevenLabs

# Local imports
from ml.config.elevenlabs import elevenlabs_config


@lru_cache(maxsize=1)
def get_elevenlabs_client() -> ElevenLabs:
    """Create and cache an ElevenLabs client.

    Returns
    -------
    ElevenLabs
        Configured ElevenLabs client.
    """
    return ElevenLabs(api_key=elevenlabs_config.API_KEY)


def transcribe_audio(
    audio_bytes: bytes,
    file_name: str,
    file_format: Optional[str] = None,
    language_code: Optional[str] = None,
) -> str:
    """Transcribe audio bytes into text using ElevenLabs STT.

    Parameters
    ----------
    audio_bytes : bytes
        Audio payload to transcribe.
    file_name : str
        File name used for the in-memory audio buffer.
    file_format : Optional[str]
        Optional format hint for the audio.
    language_code : Optional[str]
        Optional ISO-639 language code to improve transcription.

    Returns
    -------
    str
        Transcribed text.
    """
    audio_buffer = BytesIO(audio_bytes)
    audio_buffer.name = file_name
    client = get_elevenlabs_client()
    response = client.speech_to_text.convert(
        file=audio_buffer,
        model_id=elevenlabs_config.STT_MODEL_ID,
        enable_logging=elevenlabs_config.STT_ENABLE_LOGGING,
        language_code=language_code or elevenlabs_config.STT_LANGUAGE_CODE,
        file_format=file_format,
    )
    return response.text


def stream_tts_audio(
    text: str,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
    output_format: Optional[str] = None,
    optimize_streaming_latency: Optional[int] = None,
) -> Iterable[bytes]:
    """Stream audio bytes for a text using ElevenLabs TTS.

    Parameters
    ----------
    text : str
        Text to synthesize.
    voice_id : Optional[str]
        Voice ID to use for TTS.
    model_id : Optional[str]
        Model ID to use for TTS.
    output_format : Optional[str]
        Output format for audio.
    optimize_streaming_latency : Optional[int]
        Streaming latency optimization setting.

    Returns
    -------
    Iterable[bytes]
        Audio byte chunks from the ElevenLabs stream.
    """
    client = get_elevenlabs_client()
    audio_stream = client.text_to_speech.stream(
        voice_id=voice_id or elevenlabs_config.TTS_VOICE_ID,
        output_format=output_format or elevenlabs_config.TTS_OUTPUT_FORMAT,
        text=text,
        model_id=model_id or elevenlabs_config.TTS_MODEL_ID,
        optimize_streaming_latency=(
            optimize_streaming_latency
            if optimize_streaming_latency is not None
            else elevenlabs_config.TTS_OPTIMIZE_STREAMING_LATENCY
        ),
    )
    for chunk in audio_stream:
        if isinstance(chunk, bytes):
            yield chunk
