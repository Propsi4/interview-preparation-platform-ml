"""API routes for interview evaluation dispatch."""

from typing import List

from fastapi import APIRouter, HTTPException

from ml.api.schemas import EvaluationDispatchRequestSchema, EvaluationDispatchResponseSchema, VacancyInterviewScoreResponseSchema
from ml.db.engine import connect_to_db
from ml.db.repositories.chat_sessions import ChatSessionRepository
from ml.db.repositories.vacancy_interview_scores import VacancyInterviewScoreRepository
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


@router.get("/session/{session_id}/results", response_model=List[VacancyInterviewScoreResponseSchema])
async def list_evaluation_results_for_session(session_id: str) -> List[VacancyInterviewScoreResponseSchema]:
    """
    List evaluation results for a chat session.

    Parameters
    ----------
    session_id : str
        Chat session identifier.

    Returns
    -------
    list[VacancyInterviewScoreResponseSchema]
        Evaluation results for the session.
    """
    async with connect_to_db() as session:
        score_repo = VacancyInterviewScoreRepository(session)
        scores = await score_repo.list_by(chat_session_id=session_id)
    return [
        VacancyInterviewScoreResponseSchema(
            id=score.id,
            search_query_id=score.search_query_id,
            chat_session_id=score.chat_session_id,
            score=score.score,
            strong_sides=score.strong_sides,
            weak_sides=score.weak_sides,
            created_at=score.created_at,
            updated_at=score.updated_at,
        )
        for score in scores
    ]
