"""API routes for scraper operations."""

from fastapi import APIRouter, HTTPException
from ml.api.schemas import ProgressResponseSchema, ScrapeVacanciesRequestSchema, ScrapeVacanciesResponseSchema
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
