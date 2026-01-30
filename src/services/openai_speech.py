"""OpenAI speech services."""

# Standart library imports
from functools import lru_cache
from io import BytesIO
from typing import Iterable, Optional

# Thirdparty imports
from openai import OpenAI

# Local imports
from src.config.openai import openai_config


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """Create and cache an OpenAI client.

    Returns
    -------
    OpenAI
        Configured OpenAI client.
    """
    return OpenAI(api_key=openai_config.API_KEY)


def _resolve_tts_format(output_format: Optional[str]) -> str:
    """Map output format identifiers to OpenAI TTS formats.

    Parameters
    ----------
    output_format : Optional[str]
        Output format identifier.

    Returns
    -------
    str
        OpenAI-compatible TTS format.
    """
    if not output_format:
        return "mp3"
    normalized_format = output_format.lower()
    if "pcm" in normalized_format:
        return "pcm"
    if "wav" in normalized_format:
        return "wav"
    if "ogg" in normalized_format or "opus" in normalized_format:
        return "opus"
    if "flac" in normalized_format:
        return "flac"
    if "aac" in normalized_format:
        return "aac"
    return "mp3"


def transcribe_audio(
    audio_bytes: bytes,
    file_name: str,
    file_format: Optional[str] = None,
    language_code: Optional[str] = None,
) -> str:
    """Transcribe audio bytes into text using OpenAI Whisper.

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
    _ = file_format
    audio_buffer = BytesIO(audio_bytes)
    audio_buffer.name = file_name
    client = get_openai_client()
    response = client.audio.transcriptions.create(
        model=openai_config.STT_MODEL,
        file=audio_buffer,
        language=language_code,
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("OpenAI transcription response missing text.")
    return text


def stream_tts_audio(
    text: str,
    voice_id: Optional[str] = None,
    model_id: Optional[str] = None,
    speed: Optional[float] = None,
    output_format: Optional[str] = None,
) -> Iterable[bytes]:
    """Stream synthesized speech using OpenAI TTS.

    Parameters
    ----------
    text : str
        Text to synthesize.
    voice_id : Optional[str]
        Voice to use for TTS.
    model_id : Optional[str]
        Model ID to use for TTS.
    speed : Optional[float]
        Speed for TTS.
    output_format : Optional[str]
        Output format for audio.

    Returns
    -------
    Iterable[bytes]
        Audio byte chunks from the OpenAI response.
    """
    client = get_openai_client()
    response = client.audio.speech.create(
        model=model_id or openai_config.TTS_MODEL,
        voice=voice_id or openai_config.TTS_VOICE,
        input=text,
        instructions=openai_config.TTS_INSTRUCTIONS,
        speed=speed or openai_config.TTS_SPEED,
        response_format=_resolve_tts_format(output_format or openai_config.TTS_OUTPUT_FORMAT),
    )
    iter_bytes = getattr(response, "iter_bytes", None)
    if callable(iter_bytes):
        for chunk in iter_bytes():
            if chunk:
                yield chunk
        return
    content = getattr(response, "content", None)
    if isinstance(content, (bytes, bytearray)) and content:
        yield bytes(content)
        return
    if isinstance(response, (bytes, bytearray)) and response:
        yield bytes(response)
