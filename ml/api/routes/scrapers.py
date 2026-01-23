"""API routes for scraper operations."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from ml.api.schemas import ProgressResponseSchema, ScrapeVacanciesRequestSchema, ScrapeVacanciesResponseSchema
from ml.db.engine import connect_to_db
from ml.db.models.search_query import SearchQueryModel
from ml.db.models.vacancies import VacancyModel
from ml.jobs.celery_app import celery_app

router = APIRouter()


@router.post("/scrape-vacancies", response_model=ScrapeVacanciesResponseSchema, status_code=202)
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
    async with connect_to_db() as session:
        search_query = SearchQueryModel(query=payload.search_query)
        session.add(search_query)
        await session.commit()
        await session.refresh(search_query)

        celery_app.send_task(
            name="scrapers.dou.scrape_vacancies_overview",
            kwargs={"search_query_id": search_query.id, "query": payload.search_query},
        )
        return ScrapeVacanciesResponseSchema(search_query_id=search_query.id)


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
    async with connect_to_db() as session:
        search_query = await session.get(SearchQueryModel, search_query_id)
        if search_query is None:
            raise HTTPException(status_code=404, detail="Search query not found")

        stmt = select(func.count()).select_from(VacancyModel).where(VacancyModel.search_query_id == search_query_id)
        processed_results = int(await session.scalar(stmt) or 0)
        total_results = search_query.total_results
        progress_value = 0.0
        if total_results and total_results > 0:
            progress_value = round(min(processed_results / total_results, 1.0), 1)

        return ProgressResponseSchema(
            search_query_id=search_query_id,
            progress=progress_value,
            total_results=total_results,
            processed_results=processed_results,
        )
