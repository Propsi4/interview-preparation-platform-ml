"""API request and response schemas."""


from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class ScrapeVacanciesRequestSchema(BaseModel):
    """Request body for scraping vacancies.

    Parameters
    ----------
    search_query : str
        Search query string (e.g., "HR").
    """

    search_query: str = Field(min_length=1, description="Search query string")

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"search_query": "Data Scientist"}})


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

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"search_query_id": 1, "progress": 0.5, "total_results": 100, "processed_results": 50}})


class StatusResponseSchema(BaseModel):
    """Status response schema."""

    status: Literal["ok", "error"] = Field(..., description="Status type")
    message: str = Field(..., description="Status message")
