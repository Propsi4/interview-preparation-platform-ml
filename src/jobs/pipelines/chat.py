"""Pipelines for technical interview chat endpoints."""

import json
import time
from typing import AsyncGenerator

import dspy
from fastapi.responses import StreamingResponse

from src.agents.implementations.technical_interview import (
    InterviewTurnRequestSchema,
    TechnicalInterviewAgent,
    TechnicalInterviewResponseSchema,
)
from src.api.schemas import TechnicalInterviewChatRequestSchema
from src.config.app import app_config
from src.config.openai import openai_config
from src.conversation_history.manager import ConversationHistoryManager
from src.conversation_history.summarizer import ChatHistorySummarizer
from src.core.logging import logger
from src.db.engine import connect_to_db
from src.db.repositories.chat_sessions import ChatSessionRepository
from src.db.repositories.vacancies import VacancyRepository
from src.utils import extract_request_cost, persist_chat_and_cost

history_manager = ConversationHistoryManager()


class InterviewAlreadyFinishedError(RuntimeError):
    """Raised when inference is requested for a finished interview."""


async def ensure_interview_not_finished(session_id: str) -> None:
    """
    Ensure the interview is still active for a session.

    Parameters
    ----------
    session_id : str
        Chat session identifier.

    Returns
    -------
    None
        Raises InterviewAlreadyFinishedError when the interview is finished.
    """
    async with connect_to_db() as session:
        session_repo = ChatSessionRepository(session)
        session_model = await session_repo.get_by_session_id(session_id)
        if session_model is not None and session_model.interview_finished:
            raise InterviewAlreadyFinishedError("Interview already finished for this session.")


def _resolve_llm_config(payload: TechnicalInterviewChatRequestSchema) -> tuple[str, float, dict]:
    """
    Resolve LLM configuration overrides from the payload.

    Parameters
    ----------
    payload : TechnicalInterviewChatRequestSchema
        Request payload containing optional LLM overrides.

    Returns
    -------
    tuple[str, float, dict]
        Tuple of model, temperature, and additional kwargs.
    """
    llm_model = openai_config.LLM_MODEL
    llm_temperature = openai_config.LLM_TEMPERATURE
    additional_llm_kwargs = dict(openai_config.ADDITIONAL_LLM_KWARGS or {})

    overrides = payload.llm_config_override
    if overrides is None:
        return llm_model, llm_temperature, additional_llm_kwargs

    if overrides.llm_model is not None:
        llm_model = overrides.llm_model
    if overrides.llm_temperature is not None:
        llm_temperature = overrides.llm_temperature
    if overrides.additional_llm_kwargs is not None:
        additional_llm_kwargs.update(overrides.additional_llm_kwargs)

    return llm_model, llm_temperature, additional_llm_kwargs


async def _load_vacancy_descriptions(search_query_id: int) -> list[str]:
    """
    Load vacancy descriptions for a search query.

    Uses processed technical requirements when available.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.

    Returns
    -------
    list[str]
        Collected vacancy descriptions.
    """
    async with connect_to_db() as session:
        vacancy_repo = VacancyRepository(session)
        return await vacancy_repo.list_processed_descriptions(search_query_id)


async def _build_request_payload(
    session_id: str,
    payload: TechnicalInterviewChatRequestSchema,
) -> InterviewTurnRequestSchema:
    """
    Build the interview request with auto-populated chat history.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : TechnicalInterviewChatRequestSchema
        Interview turn input (search_query_id and query).

    Returns
    -------
    InterviewTurnRequestSchema
        Request payload including chat history.
    """
    chat_history = await history_manager.get_messages_for_session(session_id)

    # Summarize history if needed
    summarizer = ChatHistorySummarizer(max_history_len=app_config.MAX_CHAT_HISTORY_LEN)
    chat_history = summarizer.summarize(chat_history)

    return InterviewTurnRequestSchema(
        search_query_id=payload.search_query_id,
        chat_history=chat_history,
        query=payload.query,
    )


async def run_technical_interview(
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

    Returns
    -------
    TechnicalInterviewResponseSchema
        Agent response with completion flag.
    """
    start_time = time.time()
    llm_model, llm_temperature, additional_llm_kwargs = _resolve_llm_config(payload)
    vacancy_descriptions = await _load_vacancy_descriptions(payload.search_query_id)
    request = await _build_request_payload(session_id, payload)
    agent = TechnicalInterviewAgent()

    lm = dspy.LM(
        model=llm_model,
        temperature=llm_temperature,
        **additional_llm_kwargs,
    )

    with dspy.context(lm=lm, track_usage=True):
        start_index = len(getattr(lm, "history", []) or [])
        prediction = agent(
            vacancy_descriptions=vacancy_descriptions,
            chat_history=request.chat_history,
            query=request.query,
        )
        request_cost = extract_request_cost(lm, start_index)
        logger.debug(f"Request cost: {request_cost}")
    total_time = time.time() - start_time
    logger.debug(f"Technical interview response time: {total_time:.4f}s")

    response = TechnicalInterviewResponseSchema(
        interview_finished=getattr(prediction, "interview_finished", False),
        response=getattr(prediction, "response", ""),
    )

    await persist_chat_and_cost(
        session_id=session_id,
        user_message=payload.query,
        response_text=response.response,
        request_cost=request_cost,
        search_query_id=payload.search_query_id,
        interview_finished=response.interview_finished,
    )

    return response


def stream_technical_interview(
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

    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in iter_technical_interview_events(session_id=session_id, payload=payload):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


async def iter_technical_interview_events(
    session_id: str,
    payload: TechnicalInterviewChatRequestSchema,
) -> AsyncGenerator[dict, None]:
    """
    Stream technical interview events as structured dictionaries.

    Parameters
    ----------
    session_id : str
        Chat session identifier.
    payload : TechnicalInterviewChatRequestSchema
        Interview turn input (search_query_id and query).

    Yields
    ------
    dict
        Stream event payload containing tokens or completion.
    """
    try:
        start_time = time.time()
        first_token_received = False
        llm_model, llm_temperature, additional_llm_kwargs = _resolve_llm_config(payload)
        vacancy_descriptions = await _load_vacancy_descriptions(payload.search_query_id)
        request = await _build_request_payload(session_id, payload)
        agent = TechnicalInterviewAgent()

        lm = dspy.LM(
            model=llm_model,
            temperature=llm_temperature,
            **additional_llm_kwargs,
        )

        with dspy.context(lm=lm, track_usage=True):
            start_index = len(getattr(lm, "history", []) or [])
            stream_agent = dspy.streamify(
                agent,
                stream_listeners=[
                    dspy.streaming.StreamListener(signature_field_name="response"),
                    dspy.streaming.StreamListener(signature_field_name="reasoning"),
                ],
                is_async_program=True,
            )

            async for chunk in stream_agent(
                vacancy_descriptions=vacancy_descriptions,
                chat_history=request.chat_history,
                query=request.query,
            ):
                if isinstance(chunk, dspy.streaming.StreamResponse):
                    if not first_token_received:
                        time_to_first_token = time.time() - start_time
                        logger.debug(f"Time to first token: {time_to_first_token:.4f}s")
                        first_token_received = True
                    event = {
                        "status": "success",
                        "session_id": session_id,
                        "data": {"token": chunk.chunk},
                    }
                    if chunk.signature_field_name == "reasoning":
                        event["type"] = "reasoning"
                    else:
                        event["type"] = "answer"
                    yield event
                elif isinstance(chunk, dspy.Prediction):
                    response_schema = TechnicalInterviewResponseSchema(
                        interview_finished=getattr(chunk, "interview_finished", False),
                        response=getattr(chunk, "response", ""),
                    )

                    complete_event = {
                        "type": "complete",
                        "status": "success",
                        "session_id": session_id,
                        "data": response_schema.model_dump(),
                    }
                    yield complete_event
                    total_time = time.time() - start_time
                    logger.debug(f"Technical interview stream total time: {total_time:.4f}s")

                    # FIXME: Price is not calculated when using streamify
                    request_cost = extract_request_cost(lm, start_index)
                    logger.debug(f"Request cost: {request_cost}")
                    await persist_chat_and_cost(
                        session_id=session_id,
                        user_message=payload.query,
                        response_text=response_schema.response,
                        request_cost=request_cost,
                        search_query_id=payload.search_query_id,
                        interview_finished=response_schema.interview_finished,
                    )
    except Exception as e:
        logger.error(f"Error running technical interview stream for session {session_id}: {e}")
        error_event = {
            "type": "error",
            "status": "error",
            "session_id": session_id,
            "data": {"error": "Internal server error"},
        }
        yield error_event
