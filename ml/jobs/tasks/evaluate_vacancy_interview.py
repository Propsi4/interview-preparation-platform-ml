"""Celery task for evaluating interview performance against a vacancy."""

import asyncio
from typing import Any, List

import dspy
from langchain_core.messages import BaseMessage

from ml.agents.implementations.assessment import VacancyInterviewAssessmentAgent, VacancyInterviewAssessmentSchema
from ml.config.openai import openai_config
from ml.core.logging import logger
from ml.db.engine import connect_to_db
from ml.db.models.vacancy_interview_score import VacancyInterviewScoreModel
from ml.db.repositories.vacancy_interview_scores import VacancyInterviewScoreRepository
from ml.jobs.celery_app import celery_app


def _normalize_score(raw_score: Any) -> float:
    """
    Normalize assessment score into a 0.0-1.0 float with 1 decimal place.

    Parameters
    ----------
    raw_score : Any
        Raw score value from the model output.

    Returns
    -------
    float
        Normalized score in range 0.0-1.0.
    """
    try:
        score_value = float(raw_score)
    except (TypeError, ValueError):
        score_value = 0.0
    score_value = max(0.0, min(1.0, score_value))
    return round(score_value, 1)


def _normalize_assessment(response_obj: Any) -> VacancyInterviewAssessmentSchema:
    """
    Normalize raw DSPy output into the assessment schema.

    Parameters
    ----------
    response_obj : Any
        Raw response from the agent prediction.

    Returns
    -------
    VacancyInterviewAssessmentSchema
        Normalized assessment output.
    """
    if isinstance(response_obj, VacancyInterviewAssessmentSchema):
        assessment = response_obj
    elif isinstance(response_obj, dict):
        assessment = VacancyInterviewAssessmentSchema(**response_obj)
    else:
        assessment = VacancyInterviewAssessmentSchema(score=0.0, strong_sides=None, weak_sides=None)

    normalized_score = _normalize_score(assessment.score)
    return VacancyInterviewAssessmentSchema(
        score=normalized_score,
        strong_sides=assessment.strong_sides or None,
        weak_sides=assessment.weak_sides or None,
    )


@celery_app.task(
    name="assessment.evaluate_vacancy_interview",
    default_retry_delay=5,
    max_retries=3,
)
def evaluate_vacancy_interview(
    vacancy_description: str,
    chat_history: List[BaseMessage],
    search_query_id: int,
    chat_session_id: str,
) -> None:
    """
    Evaluate interview performance against a vacancy description.

    Parameters
    ----------
    vacancy_description : str
        Vacancy description to evaluate.
    chat_history : list[BaseMessage]
        Chat history represented as dictionaries.
    search_query_id : int
        Search query identifier.
    chat_session_id : str
        Chat session identifier.

    Returns
    -------
    None
        This task persists the evaluation result.
    """
    if not vacancy_description:
        logger.warning("Skipping assessment: empty vacancy description")
        return

    agent = VacancyInterviewAssessmentAgent()

    lm_kwargs: dict = {}
    if openai_config.LLM_MAX_TOKENS is not None:
        lm_kwargs["max_tokens"] = openai_config.LLM_MAX_TOKENS
    if openai_config.ADDITIONAL_LLM_KWARGS:
        lm_kwargs.update(openai_config.ADDITIONAL_LLM_KWARGS)

    lm = dspy.LM(
        model=openai_config.LLM_MODEL,
        temperature=openai_config.LLM_TEMPERATURE,
        **lm_kwargs,
    )

    with dspy.context(lm=lm):
        prediction = agent(
            vacancy_description=vacancy_description,
            chat_history=chat_history,
        )

    assessment = _normalize_assessment(getattr(prediction, "assessment", None))

    async def _persist_assessment() -> None:
        async with connect_to_db() as session:
            score_repo = VacancyInterviewScoreRepository(session)
            score_model = VacancyInterviewScoreModel(
                search_query_id=search_query_id,
                chat_session_id=chat_session_id,
                score=assessment.score,
                strong_sides=assessment.strong_sides,
                weak_sides=assessment.weak_sides,
            )
            await score_repo.add(score_model)
            await score_repo.commit()

    asyncio.run(_persist_assessment())
