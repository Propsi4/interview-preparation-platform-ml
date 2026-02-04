"""FastAPI Router for interview chat endpoints."""

# Thirdparty imports
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

# Local imports
from src.agents.implementations.interview import InterviewResponseSchema
from src.api.schemas import InterviewChatRequestSchema
from src.jobs.pipelines.chat import (
    InterviewAlreadyFinishedError,
    ensure_interview_not_finished,
    run_interview,
    stream_interview,
)
from src.core.logging import logger
router = APIRouter()


@router.post("/interview/{session_id}", response_model=InterviewResponseSchema)
async def chat_with_interview_agent(
    session_id: str,
    payload: InterviewChatRequestSchema,
) -> InterviewResponseSchema:
    """
    Run an interview turn and persist chat history.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : InterviewChatRequestSchema
        Interview turn input (search_query_id and query).
    """
    try:
        await ensure_interview_not_finished(session_id)
        return await run_interview(session_id=session_id, payload=payload)
    except InterviewAlreadyFinishedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to run technical interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to run technical interview") from e


@router.post("/interview/{session_id}/stream")
async def chat_with_interview_agent_stream(
    session_id: str,
    payload: InterviewChatRequestSchema,
) -> StreamingResponse:
    """
    Run an interview turn and stream the response.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : InterviewChatRequestSchema
        Interview turn input (search_query_id and query).

    Returns
    -------
    StreamingResponse
        SSE stream with token events and final InterviewResponseSchema payload.
    """
    try:
        await ensure_interview_not_finished(session_id)
        return stream_interview(session_id=session_id, payload=payload)
    except InterviewAlreadyFinishedError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to stream technical interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream technical interview") from e
