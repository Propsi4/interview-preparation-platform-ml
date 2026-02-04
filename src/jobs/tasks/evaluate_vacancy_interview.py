"""Celery task for evaluating interview performance against a vacancy."""

import asyncio
from typing import Any, Dict, List

import dspy

from src.agents.implementations.assessment import VacancyInterviewAssessmentAgent, VacancyInterviewAssessmentSchema
from src.config.openai import openai_config
from src.core.logging import logger
from src.db.engine import connect_to_db
from src.db.models.vacancy_interview_score import VacancyInterviewScoreModel
from src.db.repositories.vacancy_interview_scores import VacancyInterviewScoreRepository
from src.jobs.celery_app import celery_app
from src.conversation_history.utils import dicts_to_langchain_messages


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
    chat_history: List[Dict[str, str]],
    search_query_id: int,
    chat_session_id: str,
    vacancy_id: int,
) -> VacancyInterviewAssessmentSchema | None:
    """
    Evaluate interview performance against a vacancy description.

    Parameters
    ----------
    vacancy_description : str
        Vacancy description to evaluate.
    chat_history : List[Dict[str, str]]
        Chat history represented as dictionaries with "role" and "content" keys.
    search_query_id : int
        Search query identifier.
    chat_session_id : str
        Chat session identifier.
    vacancy_id : int
        Vacancy identifier.

    Returns
    -------
    VacancyInterviewAssessmentSchema | None
        Assessment result or None if skipped.
    """
    if not vacancy_description:
        logger.warning(f"Skipping assessment: vacancy {vacancy_id} not found or empty description")
        return None

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
            chat_history=dicts_to_langchain_messages(chat_history),
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
                vacancy_id=vacancy_id,
            )
            await score_repo.add(score_model)
            await score_repo.commit()

    asyncio.run(_persist_assessment())

    return assessment
