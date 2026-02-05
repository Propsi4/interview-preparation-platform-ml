"""Celery task for unifying vacancy requirements.

Examples
--------
>>> # Start worker:
>>> # celery -A src.jobs.celery_app.celery_app worker -Q scrapers -l info
>>> # Enqueue task:
>>> # from src.jobs.tasks.unify_requirements import unify_requirements_task
>>> # unify_requirements_task.delay(1)
"""

import asyncio

from src.agents.implementations.requirements_aggregator import RequirementsAggregator
from src.config.openai import openai_config
from src.core.logging import logger
from src.db.engine import connect_to_db
from src.db.models.unified_requirements import UnifiedRequirementsModel
from src.db.repositories.unified_requirements import UnifiedRequirementsRepository
from src.db.repositories.vacancies import VacancyRepository
from src.jobs.celery_app import celery_app
import dspy


@celery_app.task(
    name="agggregation.unify_requirements",
    rate_limit="10/m",
    default_retry_delay=10,
    max_retries=3,
)
def unify_requirements_task(search_query_id: int) -> int:
    """
    Unify requirements for a search query.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.

    Returns
    -------
    int
        Unified requirements ID.
    """

    async def _unify_requirements(search_query_id: int) -> int:
        async with connect_to_db() as session:
            vacancy_repo = VacancyRepository(session)
            unified_repo = UnifiedRequirementsRepository(session)

            # 1. Fetch all processed descriptions
            descriptions = await vacancy_repo.list_processed_descriptions(search_query_id)
            descriptions = [d for d in descriptions if d]

            if not descriptions:
                logger.warning(f"No descriptions found for search query {search_query_id}")
                return -1

            # 2. Check if already unified?
            # Ideally we want to update it if it exists or create new.
            # For now, let's check if it exists and update, or create.
            existing = await unified_repo.get_by_search_query_id(search_query_id)

            # 3. Aggregate using LLM
            lm_kwargs: dict = {}
            if openai_config.LLM_MAX_TOKENS is not None:
                lm_kwargs["max_tokens"] = openai_config.LLM_MAX_TOKENS
            if openai_config.ADDITIONAL_LLM_KWARGS:
                lm_kwargs.update(openai_config.ADDITIONAL_LLM_KWARGS or {})

            lm = dspy.LM(
                model=openai_config.LLM_MODEL,
                temperature=0.0,  # Strict aggregation
                **lm_kwargs,
            )

            aggregator = RequirementsAggregator()
            with dspy.context(lm=lm):
                prediction = aggregator(processed_descriptions=descriptions)

            unified_text = getattr(prediction, "aggregated_requirements", "")

            if existing:
                existing.requirements = unified_text
                await unified_repo.commit()
                logger.info(f"Updated unified requirements for search query {search_query_id}")
                return existing.id
            else:
                new_model = UnifiedRequirementsModel(search_query_id=search_query_id, requirements=unified_text)
                await unified_repo.add(new_model)
                await unified_repo.commit()
                logger.info(f"Created unified requirements for search query {search_query_id}")
                return new_model.id

    unified_requirements_id = asyncio.run(_unify_requirements(search_query_id))
    return unified_requirements_id
