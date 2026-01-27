"""Pipelines for technical interview chat endpoints."""

import json
import time
from typing import Any, AsyncGenerator

import dspy
from fastapi.responses import StreamingResponse

from ml.agents.implementations.technical_interview import (
    InterviewTurnRequestSchema,
    TechnicalInterviewAgent,
    TechnicalInterviewResponseSchema,
)
from ml.api.schemas import TechnicalInterviewChatRequestSchema
from ml.config.openai import openai_config
from ml.conversation_history.manager import ConversationHistoryManager
from ml.core.logging import logger
from ml.db.engine import connect_to_db
from ml.db.repositories.vacancies import VacancyRepository
from ml.utils import extract_request_cost, persist_chat_and_cost

history_manager = ConversationHistoryManager()


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
        return await vacancy_repo.list_descriptions(search_query_id)


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
    return InterviewTurnRequestSchema(
        search_query_id=payload.search_query_id,
        chat_history=chat_history,
        query=payload.query,
    )


def _to_response_schema(response_obj: Any) -> TechnicalInterviewResponseSchema:
    """
    Normalize agent response into the API response schema.

    Parameters
    ----------
    response_obj : Any
        Raw response from the agent prediction.

    Returns
    -------
    TechnicalInterviewResponseSchema
        Normalized response schema.
    """
    if isinstance(response_obj, TechnicalInterviewResponseSchema):
        return response_obj
    if isinstance(response_obj, dict):
        return TechnicalInterviewResponseSchema(**response_obj)
    return TechnicalInterviewResponseSchema(
        interview_finished=False,
        response="" if response_obj is None else str(response_obj),
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

    response = _to_response_schema(getattr(prediction, "response", None))

    await persist_chat_and_cost(
        session_id=session_id,
        user_message=payload.query,
        response_text=response.response,
        request_cost=request_cost,
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
                        yield f"data: {json.dumps(event)}\n\n"
                    elif isinstance(chunk, dspy.Prediction):
                        response_schema = _to_response_schema(getattr(chunk, "response", None))
                        response_payload = response_schema.model_dump()
                        response_text = response_schema.response

                        complete_event = {
                            "type": "complete",
                            "status": "success",
                            "session_id": session_id,
                            "data": response_payload,
                        }
                        yield f"data: {json.dumps(complete_event)}\n\n"
                        total_time = time.time() - start_time
                        logger.debug(f"Technical interview stream total time: {total_time:.4f}s")

                        # FIXME: Price is not calculated when using streamify
                        request_cost = extract_request_cost(lm, start_index)
                        logger.debug(f"Request cost: {request_cost}")
                        await persist_chat_and_cost(
                            session_id=session_id,
                            user_message=payload.query,
                            response_text=response_text,
                            request_cost=request_cost,
                            interview_finished=response_schema.interview_finished,
                        )
        except Exception as exc:
            logger.error(f"Error running technical interview stream for session {session_id}: {exc}", exc_info=True)
            error_event = {
                "type": "error",
                "status": "error",
                "session_id": session_id,
                "data": {"error": "Internal server error"},
            }
            yield f"data: {json.dumps(error_event)}\n\n"

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
