"""API request and response schemas."""


from pydantic import BaseModel, Field


class ScrapeVacanciesRequest(BaseModel):
    """Request body for scraping vacancies.

    Parameters
    ----------
    query : str
        Search query string (e.g., "HR").
    """

    query: str = Field(min_length=1, description="Search query string")


class ScrapeVacanciesResponse(BaseModel):
    """Response body for scraping request.

    Parameters
    ----------
    search_query_id : int
        Identifier of the search query.
    """

    search_query_id: int = Field(..., description="Search query identifier")


class ProgressResponse(BaseModel):
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


class HealthResponse(BaseModel):
    """Health check response.

    Parameters
    ----------
    status : str
        Service status string.
    """

    status: str = Field(..., description="Health status")
