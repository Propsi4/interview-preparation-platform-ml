"""Pipeline for dispatching vacancy interview assessments."""

from typing import List

from langchain_core.messages import BaseMessage

from ml.conversation_history.manager import ConversationHistoryManager
from ml.conversation_history.utils import langchain_messages_to_dicts
from ml.core.logging import logger
from ml.db.engine import connect_to_db
from ml.db.repositories.vacancies import VacancyRepository
from ml.jobs.celery_app import celery_app

history_manager = ConversationHistoryManager()


async def dispatch_vacancy_assessments(chat_session_id: str, search_query_id: int) -> int:
    """
    Dispatch assessment tasks for each vacancy in a search query.

    Parameters
    ----------
    chat_session_id : str
        Chat session identifier.
    search_query_id : int
        Search query identifier.

    Returns
    -------
    int
        Number of tasks dispatched.
    """
    async with connect_to_db() as session:
        vacancy_repo = VacancyRepository(session)
        vacancies = await vacancy_repo.list_by_search_query_id(search_query_id)

    chat_history: List[BaseMessage] = await history_manager.get_messages_for_session(chat_session_id)

    dispatched = 0
    for vacancy in vacancies:
        if not vacancy.description:
            continue
        celery_app.send_task(
            name="assessment.evaluate_vacancy_interview",
            kwargs={
                "vacancy_description": vacancy.description,
                "chat_history": langchain_messages_to_dicts(chat_history),
                "search_query_id": search_query_id,
                "chat_session_id": chat_session_id,
            },
        )
        dispatched += 1

    logger.info(
        f"Dispatched {dispatched} vacancy assessment tasks for session={chat_session_id}, query={search_query_id}",
    )
    return dispatched
