"""Pipelines for scraper operations."""

from src.api.schemas import ProgressResponseSchema, ScrapeVacanciesRequestSchema, ScrapeVacanciesResponseSchema
from src.db.engine import connect_to_db
from src.db.models.search_query import SearchQueryModel
from src.db.repositories.search_queries import SearchQueryRepository
from src.db.repositories.vacancies import VacancyRepository
from src.jobs.celery_app import celery_app


async def enqueue_vacancy_scrape(payload: ScrapeVacanciesRequestSchema) -> ScrapeVacanciesResponseSchema:
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
        query_repo = SearchQueryRepository(session)
        search_query = SearchQueryModel(query=payload.search_query)
        await query_repo.add(search_query)
        await query_repo.commit()
        await query_repo.refresh(search_query)

        celery_app.send_task(
            name="scrapers.dou.scrape_vacancies_overview",
            kwargs={"search_query_id": search_query.id, "query": payload.search_query},
        )
        return ScrapeVacanciesResponseSchema(search_query_id=search_query.id)


async def get_scrape_progress(search_query_id: int) -> ProgressResponseSchema:
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
        query_repo = SearchQueryRepository(session)
        vacancy_repo = VacancyRepository(session)
        search_query = await query_repo.get(search_query_id)
        if search_query is None:
            raise ValueError("Search query not found")

        processed_results = await vacancy_repo.count_by_search_query_id(search_query_id, scrapped=True)
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
