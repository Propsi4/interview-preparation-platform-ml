"""Celery task package for background jobs."""

from ml.jobs.tasks import scrape_dou_vacancies_overview, scrape_dou_vacancy_details

__all__ = [
    "scrape_dou_vacancies_overview",
    "scrape_dou_vacancy_details",
]
