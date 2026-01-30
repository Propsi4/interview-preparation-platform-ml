"""Celery task for scraping dou.ua vacancies.

Examples
--------
>>> # Start worker:
>>> # celery -A src.jobs.celery_app.celery_app worker -Q scrapers -l info
>>> # Enqueue task:
>>> # from src.jobs.tasks.scrape_dou import scrape_dou
>>> # scrape_dou.delay("HR")
"""

import asyncio

from typing import List
from src.db.engine import connect_to_db
from src.db.models.vacancies import VacancyModel
from src.db.repositories.search_queries import SearchQueryRepository
from src.db.repositories.vacancies import VacancyRepository
from src.jobs.celery_app import celery_app
from src.scrapers.implementations.dou import DouScraper
from src.core.logging import logger


@celery_app.task(
    name="scrapers.dou.scrape_vacancies_overview",
    rate_limit="40/m",
    default_retry_delay=5,
    max_retries=3,
)
def scrape_vacancies_overview(search_query_id: int, query: str) -> int:
    """
    Run the dou.ua scraper for a query.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.
    query : str
        Search query to submit (e.g., "HR").

    Returns
    -------
    int
        Count of vacancies persisted.
    """
    scraper = DouScraper()
    response = asyncio.run(scraper.arun(query))

    async def _update_search_query(search_query_id: int, total_results: int) -> None:
        async with connect_to_db() as session:
            query_repo = SearchQueryRepository(session)
            search_query = await query_repo.get(search_query_id)
            if search_query is None:
                raise ValueError(f"Search query {search_query_id} not found")
            await query_repo.update_total_results(search_query, total_results)
            await query_repo.commit()
            logger.info(f"Search query {search_query.id} updated with total_results={total_results}")

    async def _add_vacancies(search_query_id: int, vacancies_urls: List[str]) -> List[int]:
        async with connect_to_db() as session:
            vacancies = [VacancyModel(search_query_id=search_query_id, url=url) for url in vacancies_urls]
            vacancy_repo = VacancyRepository(session)
            await vacancy_repo.add_all(vacancies)
            await vacancy_repo.flush()
            await vacancy_repo.commit()
            logger.info(f"Added {len(vacancies)} vacancies for search query {search_query_id}")
            return [vacancy.id for vacancy in vacancies]

    asyncio.run(_update_search_query(search_query_id, response.total_results))
    vacancies_ids = asyncio.run(_add_vacancies(search_query_id, response.vacancies_urls))

    for vacancy_id in vacancies_ids:
        celery_app.send_task(
            name="scrapers.dou.scrape_vacancy_details",
            kwargs={
                "vacancy_id": vacancy_id,
            },
        )
    return response
