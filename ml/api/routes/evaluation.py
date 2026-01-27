"""API routes for interview evaluation dispatch."""

from fastapi import APIRouter

from ml.api.schemas import EvaluationDispatchRequestSchema, EvaluationDispatchResponseSchema
from ml.jobs.pipelines.evaluation import dispatch_vacancy_assessments

router = APIRouter()


@router.post("/evaluation/dispatch", response_model=EvaluationDispatchResponseSchema, status_code=202)
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
    dispatched = await dispatch_vacancy_assessments(
        chat_session_id=payload.chat_session_id,
        search_query_id=payload.search_query_id,
    )
    return EvaluationDispatchResponseSchema(dispatched_tasks=dispatched)
