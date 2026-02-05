"""Celery task package for background jobs."""

from .scrape_dou_vacancies_overview import scrape_vacancies_overview as scrape_dou_vacancies_overview
from .scrape_dou_vacancy_details import scrape_vacancy_details as scrape_dou_vacancy_details
from .evaluate_vacancy_interview import evaluate_vacancy_interview
from .unify_requirements import unify_requirements_task

__all__ = [
    "scrape_dou_vacancies_overview",
    "scrape_dou_vacancy_details",
    "evaluate_vacancy_interview",
    "unify_requirements_task",
]
