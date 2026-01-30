"""Celery task package for background jobs."""

from src.jobs.tasks import scrape_dou_vacancies_overview, scrape_dou_vacancy_details, evaluate_vacancy_interview

__all__ = [
    "scrape_dou_vacancies_overview",
    "scrape_dou_vacancy_details",
    "evaluate_vacancy_interview",
]
