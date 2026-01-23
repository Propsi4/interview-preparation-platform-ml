"""Schemas for vacancies."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List


class VacancySchema(BaseModel):
    """Schema for a scraped vacancy."""

    title: str = Field(description="Vacancy title")
    company: str = Field(description="Vacancy company")
    location: str | None = Field(description="Vacancy location")
    description: str = Field(description="Vacancy description")
    url: str = Field(description="Vacancy URL")

    model_config = ConfigDict(from_attributes=True)


class VacanciesOverviewSchema(BaseModel):
    """Schema for a response of scraping vacancies."""

    query: str = Field(description="Search query")
    total_results: int = Field(description="Total results")
    vacancies_urls: List[str] = Field(description="List of vacancies URLs")
