"""API request and response schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class ScrapeVacanciesRequestSchema(BaseModel):
    """Request body for scraping vacancies.

    Parameters
    ----------
    search_query : str
        Search query string (e.g., "HR").
    """

    search_query: str = Field(min_length=1, description="Search query string")

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"search_query": "Data Scientist"}})


class ConfigableLLMRequestSchema(BaseModel):
    """Request body for configuring an LLM."""

    llm_model: str = Field(..., description="LLM model to use for the interview")
    llm_temperature: float = Field(..., description="LLM temperature to use for the interview")
    additional_llm_kwargs: dict = Field(..., description="Additional LLM kwargs to use for the interview")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "llm_model": "openai/gpt-4.1-mini",
                "llm_temperature": 0.0,
                "additional_llm_kwargs": {"max_tokens": 32000},
            }
        },
    )


class TechnicalInterviewChatRequestSchema(BaseModel):
    """Request body for running a technical interview turn."""

    search_query_id: int = Field(..., description="Search query identifier")
    query: str = Field(..., description="Latest user input")
    llm_config_override: Optional[ConfigableLLMRequestSchema] = Field(default=None, description="LLM configuration")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "search_query_id": 1,
                "query": "Interview me on the topic of data science",
                "llm_config_override": {
                    "llm_model": "openai/gpt-4.1-mini",
                    "llm_temperature": 0.0,
                    "additional_llm_kwargs": {"max_tokens": 32000},
                },
            }
        },
    )


class SpeechStartFrameSchema(BaseModel):
    """WebSocket frame to start a speech session."""

    type: Literal["start"] = Field(default="start", description="Frame type")
    session_id: str = Field(..., description="Chat session identifier")
    search_query_id: int = Field(..., description="Search query identifier")
    tts_enabled: bool = Field(default=True, description="Enable TTS audio output")
    audio_format: Optional[str] = Field(
        default=None,
        description="Optional STT audio format hint (e.g., 'pcm_s16le_16')",
    )
    audio_file_name: str = Field(
        default="speech_input.wav",
        description="File name used for audio transcription metadata",
    )
    language_code: Optional[str] = Field(
        default=None,
        description="Optional ISO-639 language code for STT",
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "start",
                "session_id": "session_123",
                "search_query_id": 1,
                "tts_enabled": True,
                "audio_format": "other",
                "audio_file_name": "speech_input.wav",
                "language_code": "en",
            }
        },
    )


class SpeechAudioFrameSchema(BaseModel):
    """WebSocket frame carrying a base64 audio chunk."""

    type: Literal["audio"] = Field(default="audio", description="Frame type")
    chunk: str = Field(..., description="Base64-encoded audio chunk")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"type": "audio", "chunk": "base64-encoded-audio-bytes"},
        },
    )


class SpeechEndFrameSchema(BaseModel):
    """WebSocket frame to finalize a speech session."""

    type: Literal["end"] = Field(default="end", description="Frame type")

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"type": "end"}})


class SpeechTranscriptionResponseSchema(BaseModel):
    """Response body for speech transcription."""

    text: str = Field(..., description="Transcribed text")


class SpeechSynthesisRequestSchema(BaseModel):
    """Request body for speech synthesis."""

    text: str = Field(..., min_length=1, description="Text to synthesize")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"text": "Explain how a binary search works."}},
    )


class SpeechStreamEventSchema(BaseModel):
    """WebSocket event emitted by the speech stream."""

    type: Literal[
        "transcript",
        "reasoning",
        "answer",
        "complete",
        "audio_chunk",
        "error",
        "info",
    ] = Field(..., description="Event type")
    data: dict = Field(default_factory=dict, description="Event payload")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "type": "audio_chunk",
                "data": {"chunk": "base64-encoded-audio-bytes"},
            }
        },
    )


class EvaluationDispatchRequestSchema(BaseModel):
    """Request body for dispatching vacancy interview assessments."""

    chat_session_id: str = Field(..., description="Chat session identifier")
    search_query_id: int = Field(..., description="Search query identifier")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"chat_session_id": "session_123", "search_query_id": 1}},
    )


class EvaluationDispatchResponseSchema(BaseModel):
    """Response body for dispatching vacancy interview assessments."""

    dispatched_tasks: int = Field(..., ge=0, description="Number of tasks dispatched")


class VacancyInterviewScoreResponseSchema(BaseModel):
    """Response body for vacancy interview evaluation results."""

    id: int = Field(..., description="Score record identifier")
    search_query_id: int = Field(..., description="Search query identifier")
    chat_session_id: str = Field(..., description="Chat session identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized assessment score")
    strong_sides: Optional[str] = Field(default=None, description="Highlighted strong sides of the interview")
    weak_sides: Optional[str] = Field(default=None, description="Highlighted weak sides of the interview")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "search_query_id": 42,
                "chat_session_id": "session_123",
                "score": 0.7,
                "strong_sides": "Clear communication and relevant examples.",
                "weak_sides": "Needs deeper system design explanations.",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z",
            }
        },
    )


class ScrapeVacanciesResponseSchema(BaseModel):
    """Response body for scraping request.

    Parameters
    ----------
    search_query_id : int
        Identifier of the search query.
    """

    search_query_id: int = Field(..., description="Search query identifier")


class SearchQueryResponseSchema(BaseModel):
    """Response body for search query listings."""

    id: int = Field(..., description="Search query identifier")
    query: str = Field(..., description="Search query text")
    total_results: int | None = Field(default=None, description="Total results reported by the source")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 1,
                "query": "Data Scientist",
                "total_results": 120,
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z",
            }
        },
    )


class ProgressResponseSchema(BaseModel):
    """Response body for search progress.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.
    progress : float
        Progress ratio (0.0 - 1.0).
    total_results : int | None
        Total results reported by the source.
    processed_results : int
        Number of processed vacancies.
    """

    search_query_id: int = Field(..., description="Search query identifier")
    progress: float = Field(..., ge=0.0, le=1.0, description="Completion ratio")
    total_results: int | None = Field(default=None, description="Total results from source")
    processed_results: int = Field(..., ge=0, description="Processed vacancies count")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"search_query_id": 1, "progress": 0.5, "total_results": 100, "processed_results": 50}
        },
    )


class StatusResponseSchema(BaseModel):
    """Status response schema."""

    status: Literal["ok", "error"] = Field(..., description="Status type")
    message: str = Field(..., description="Status message")
