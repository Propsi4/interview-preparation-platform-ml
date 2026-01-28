"""Configuration for ElevenLabs speech features."""

# Standart library imports
from typing import Optional

# Thirdparty imports
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class ElevenLabsConfig(BaseSettings):
    """ElevenLabs configuration values."""

    API_KEY: str = Field(..., description="ElevenLabs API key", alias="ELEVENLABS_API_KEY")
    TTS_VOICE_ID: str = Field(..., description="Default voice ID for TTS", alias="ELEVENLABS_TTS_VOICE_ID")
    TTS_MODEL_ID: str = Field(
        default="eleven_multilingual_v2",
        description="Default model ID for TTS",
        alias="ELEVENLABS_TTS_MODEL_ID",
    )
    TTS_OUTPUT_FORMAT: str = Field(
        default="mp3_44100_128",
        description="Audio output format for TTS",
        alias="ELEVENLABS_TTS_OUTPUT_FORMAT",
    )
    TTS_OPTIMIZE_STREAMING_LATENCY: int = Field(
        default=2,
        ge=0,
        le=4,
        description="Latency optimization setting for streaming TTS",
        alias="ELEVENLABS_TTS_OPTIMIZE_STREAMING_LATENCY",
    )
    STT_MODEL_ID: str = Field(
        default="scribe_v1",
        description="Default model ID for STT",
        alias="ELEVENLABS_STT_MODEL_ID",
    )
    STT_LANGUAGE_CODE: Optional[str] = Field(
        default=None,
        description="Optional ISO-639 language code for STT",
        alias="ELEVENLABS_STT_LANGUAGE_CODE",
    )
    STT_ENABLE_LOGGING: bool = Field(
        default=True,
        description="Enable ElevenLabs logging for STT requests",
        alias="ELEVENLABS_STT_ENABLE_LOGGING",
    )


elevenlabs_config = ElevenLabsConfig()
