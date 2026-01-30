"""Schemas for vacancy interview assessment."""

from pydantic import BaseModel, Field


class VacancyInterviewAssessmentSchema(BaseModel):
    """Assessment output for a vacancy interview."""

    score: float = Field(..., ge=0.0, le=1.0, description="Match score from 0.0 to 1.0. Rounded to 1 decimal place.")
    strong_sides: str | None = Field(default=None, description="Factors that increased the score")
    weak_sides: str | None = Field(default=None, description="Factors that decreased the score")
