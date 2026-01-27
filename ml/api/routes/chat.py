"""FastAPI Router for technical interview chat endpoints."""

# Thirdparty imports
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

# Local imports
from ml.agents.implementations.technical_interview import TechnicalInterviewResponseSchema
from ml.api.schemas import TechnicalInterviewChatRequestSchema
from ml.jobs.pipelines.chat import run_technical_interview, stream_technical_interview
from ml.core.logging import logger
router = APIRouter()


@router.post("/interview/{session_id}", response_model=TechnicalInterviewResponseSchema)
async def chat_with_technical_interview_agent(
    session_id: str,
    payload: TechnicalInterviewChatRequestSchema,
) -> TechnicalInterviewResponseSchema:
    """
    Run a technical interview turn and persist chat history.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : TechnicalInterviewChatRequestSchema
        Interview turn input (search_query_id and query).
    """
    try:
        return await run_technical_interview(session_id=session_id, payload=payload)
    except Exception as e:
        logger.error(f"Failed to run technical interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to run technical interview") from e


@router.post("/interview/{session_id}/stream")
async def chat_with_technical_interview_agent_stream(
    session_id: str,
    payload: TechnicalInterviewChatRequestSchema,
) -> StreamingResponse:
    """
    Run a technical interview turn and stream the response.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : TechnicalInterviewChatRequestSchema
        Interview turn input (search_query_id and query).

    Returns
    -------
    StreamingResponse
        SSE stream with token events and final TechnicalInterviewResponseSchema payload.
    """
    try:
        return stream_technical_interview(session_id=session_id, payload=payload)
    except Exception as e:
        logger.error(f"Failed to stream technical interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream technical interview") from e
