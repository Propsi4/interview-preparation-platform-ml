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
    progress: float = Field(..., ge=0.0, le=1.0, decimal_places=1, description="Completion ratio")
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
