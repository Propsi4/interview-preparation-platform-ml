"""Celery task for scraping dou.ua vacancies.

Examples
--------
>>> # Start worker:
>>> # celery -A ml.jobs.celery_app.celery_app worker -Q scrapers -l info
>>> # Enqueue task:
>>> # from ml.jobs.tasks.scrape_dou import scrape_dou
>>> # scrape_dou.delay("HR")
"""


import asyncio

from typing import List
from ml.db.engine import connect_to_db
from ml.db.models.search_query import SearchQuery
from ml.db.models.vacancies import Vacancy
from ml.jobs.celery_app import celery_app
from ml.scrapers.implementations.dou import DouScraper
from ml.core.logging import logger


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
            search_query = await session.get(SearchQuery, search_query_id)
            if search_query is None:
                raise ValueError(f"Search query {search_query_id} not found")
            search_query.total_results = total_results
            await session.commit()
            logger.info(f"Search query {search_query.id} updated with total_results={total_results}")

    async def _add_vacancies(search_query_id: int, vacancies_urls: List[str]) -> List[int]:
        async with connect_to_db() as session:
            vacancies = [Vacancy(search_query_id=search_query_id, url=url) for url in vacancies_urls]
            session.add_all(vacancies)
            await session.commit()
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
