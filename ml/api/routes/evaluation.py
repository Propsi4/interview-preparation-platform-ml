"""API routes for interview evaluation dispatch."""

from fastapi import APIRouter, HTTPException

from ml.api.schemas import EvaluationDispatchRequestSchema, EvaluationDispatchResponseSchema
from ml.db.engine import connect_to_db
from ml.db.repositories.chat_sessions import ChatSessionRepository
from ml.jobs.pipelines.evaluation import dispatch_vacancy_assessments

router = APIRouter()


@router.post("/evaluate", response_model=EvaluationDispatchResponseSchema, status_code=202)
async def dispatch_evaluation(payload: EvaluationDispatchRequestSchema) -> EvaluationDispatchResponseSchema:
    """
    Dispatch vacancy interview assessment tasks for a session.

    Parameters
    ----------
    payload : EvaluationDispatchRequestSchema
        Dispatch request containing identifiers.

    Returns
    -------
    EvaluationDispatchResponseSchema
        Count of tasks dispatched.
    """
    # if interview is not finished, raise an error
    async with connect_to_db() as session:
        session_repo = ChatSessionRepository(session)
        session_model = await session_repo.get_by_session_id(payload.chat_session_id)
        if not session_model.interview_finished:
            raise HTTPException(status_code=400, detail="Interview is not finished. Please finish the interview first and try again.")

    dispatched = await dispatch_vacancy_assessments(
        chat_session_id=payload.chat_session_id,
        search_query_id=payload.search_query_id,
    )
    return EvaluationDispatchResponseSchema(dispatched_tasks=dispatched)
