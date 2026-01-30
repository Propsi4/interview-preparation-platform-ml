"""API routes for scraper operations."""

from typing import List

from fastapi import APIRouter, HTTPException

from ml.api.schemas import ProgressResponseSchema, ScrapeVacanciesRequestSchema, ScrapeVacanciesResponseSchema, SearchQueryResponseSchema
from ml.db.engine import connect_to_db
from ml.db.repositories.search_queries import SearchQueryRepository
from ml.jobs.pipelines.scrapers import enqueue_vacancy_scrape, get_scrape_progress

router = APIRouter()


@router.post("/scrape", response_model=ScrapeVacanciesResponseSchema, status_code=202)
async def scrape_vacancies(payload: ScrapeVacanciesRequestSchema) -> ScrapeVacanciesResponseSchema:
    """
    Enqueue a vacancies scraping job.

    Parameters
    ----------
    payload : ScrapeVacanciesRequestSchema
        Scraping request payload.

    Returns
    -------
    ScrapeVacanciesResponseSchema
        Search query identifier.
    """
    return await enqueue_vacancy_scrape(payload)


@router.get("/progress/{search_query_id}", response_model=ProgressResponseSchema)
async def progress(search_query_id: int) -> ProgressResponseSchema:
    """
    Return scraping progress for a search query.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.

    Returns
    -------
    ProgressResponseSchema
        Progress metrics for the search query.
    """
    try:
        return await get_scrape_progress(search_query_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/queries", response_model=List[SearchQueryResponseSchema])
async def list_search_queries() -> List[SearchQueryResponseSchema]:
    """
    List all search queries.

    Returns
    -------
    list[SearchQueryResponseSchema]
        Search query entries.
    """
    async with connect_to_db() as session:
        repo = SearchQueryRepository(session)
        queries = await repo.list()
    return [
        SearchQueryResponseSchema(
            id=query.id,
            query=query.query,
            total_results=query.total_results,
            created_at=query.created_at,
            updated_at=query.updated_at,
        )
        for query in queries
    ]
