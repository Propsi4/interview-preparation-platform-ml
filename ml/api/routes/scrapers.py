"""API routes for scraper operations."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from ml.api.schemas import ProgressResponse, ScrapeVacanciesRequest, ScrapeVacanciesResponse
from ml.db.engine import connect_to_db
from ml.db.models.search_query import SearchQuery
from ml.db.models.vacancies import Vacancy
from ml.jobs.celery_app import celery_app

router = APIRouter()


@router.post("/scrape-vacancies", response_model=ScrapeVacanciesResponse, status_code=202)
async def scrape_vacancies(payload: ScrapeVacanciesRequest) -> ScrapeVacanciesResponse:
    """
    Enqueue a vacancies scraping job.

    Parameters
    ----------
    payload : ScrapeVacanciesRequest
        Scraping request payload.

    Returns
    -------
    ScrapeVacanciesResponse
        Search query identifier.
    """
    async with connect_to_db() as session:
        search_query = SearchQuery(query=payload.query, total_results=None, processed_results=0)
        session.add(search_query)
        await session.commit()
        await session.refresh(search_query)

        celery_app.send_task(
            name="scrapers.dou.scrape_vacancies_overview",
            kwargs={"search_query_id": search_query.id, "query": payload.query},
        )
        return ScrapeVacanciesResponse(search_query_id=search_query.id)


@router.get("/progress/{search_query_id}", response_model=ProgressResponse)
async def progress(search_query_id: int) -> ProgressResponse:
    """
    Return scraping progress for a search query.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.

    Returns
    -------
    ProgressResponse
        Progress metrics for the search query.
    """
    async with connect_to_db() as session:
        search_query = await session.get(SearchQuery, search_query_id)
        if search_query is None:
            raise HTTPException(status_code=404, detail="Search query not found")

        stmt = select(func.count()).select_from(Vacancy).where(Vacancy.search_query_id == search_query_id)
        processed_results = int(await session.scalar(stmt) or 0)
        total_results = search_query.total_results
        progress_value = 0.0
        if total_results and total_results > 0:
            progress_value = min(processed_results / total_results, 1.0)

        return ProgressResponse(
            search_query_id=search_query_id,
            progress=progress_value,
            total_results=total_results,
            processed_results=processed_results,
        )
