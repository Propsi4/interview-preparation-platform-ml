"""Celery task for scraping dou.ua vacancy details.

Examples
--------
>>> # Start worker:
>>> # celery -A ml.jobs.celery_app.celery_app worker -Q scrapers -l info
>>> # Enqueue task:
>>> # from ml.jobs.tasks.scrape_dou_vacancy_details import scrape_vacancy_details
>>> # scrape_vacancy_details.delay(1)
"""


import asyncio

from ml.db.models.vacancies import Vacancy
from ml.scrapers.schemas.vacancy import Vacancy as VacancySchema
from ml.db.engine import connect_to_db
from ml.core.logging import logger
from ml.jobs.celery_app import celery_app
from ml.scrapers.implementations.dou import DouScraper


@celery_app.task(
    name="scrapers.dou.scrape_vacancy_details",
    rate_limit="20/m",
    default_retry_delay=10,
    max_retries=3,
)
def scrape_vacancy_details(
    vacancy_id: int,
) -> VacancySchema:
    """
    Scrape vacancy details by its ID.

    Parameters
    ----------
    vacancy_id : int
        Vacancy ID to scrape details for.

    Returns
    -------
    VacancySchema
        Vacancy with updated details.
    """

    async def _scrape_vacancy(vacancy_id: int) -> Vacancy:
        async with connect_to_db() as session:
            scraper = DouScraper()
            vacancy = await session.get(Vacancy, vacancy_id)
            scraped = await scraper.scrape_vacancy(vacancy.url)

            # Update vacancy with the scraped data
            vacancy.title = scraped.title
            vacancy.company = scraped.company
            vacancy.location = scraped.location
            vacancy.description = scraped.description
            vacancy.url = scraped.url
            vacancy.scrapped = True

            await session.commit()
            logger.info(f"Vacancy {vacancy_id} updated with scraped details")
            return vacancy

    db_vacancy = asyncio.run(_scrape_vacancy(vacancy_id))
    return VacancySchema.model_validate(db_vacancy)
