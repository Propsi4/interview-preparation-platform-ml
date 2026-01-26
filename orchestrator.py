"""API router for orchestrator chat (blocking and streaming)."""

# Standart library imports
import json
import time
from typing import Any, AsyncGenerator, List

# Thirdparty imports
import dspy
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from ml.core.logging import logger

# Local imports
from pet_tool.agents.orchestrator.models import OrchestratorIO
from pet_tool.agents.orchestrator.orchestrator import OrchestratorAgent
from pet_tool.agents.orchestrator.status_manager import OrchestratorStatusProvider
from pet_tool.consts.consts import AGENT_COMPONENTS
from pet_tool.conversation_history.manager import ConversationHistoryManager
from pet_tool.conversation_history.utils import (
    dict_to_dspy_format,
    langchain_messages_to_dicts,
    tool_messages_from_flat_json,
)
from pet_tool.docs.models import File
from pet_tool.utils.utils import dspy_context

router = APIRouter()
history_manager = ConversationHistoryManager()

orchestrator_agent: OrchestratorAgent = AGENT_COMPONENTS['orchestrator'].agent


def extract_request_cost(lm: dspy.LM, start_index: int) -> float:
    """
    Sum DSPy-recorded costs for calls made after a given history index.

    Parameters
    ----------
    lm : dspy.LM
        DSPy LM instance with a ``history`` attribute.
    start_index : int
        Starting index for new history items.

    Returns
    -------
    float
        Total cost accumulated for the request.
    """
    history = getattr(lm, "history", []) or []
    total_cost = 0.0
    for item in history[start_index:]:
        if isinstance(item, dict):
            cost_value = item.get("cost")
        else:
            cost_value = getattr(item, "cost", None)
        if cost_value is None:
            continue
        try:
            total_cost += float(cost_value)
        except (TypeError, ValueError):
            continue
    return total_cost


async def persist_chat_and_cost(
    session_id: str,
    user_message: str,
    response_text: str,
    trajectory: Any,
    request_cost: float,
) -> None:
    """
    Persist chat messages and update session pricing if applicable.

    Parameters
    ----------
    session_id : str
        The chat session identifier.
    user_message : str
        Raw user message content.
    response_text : str
        Final assistant response text.
    trajectory : dict
        DSPy trajectory with tool calls for conversion to tool messages.
    request_cost : float
        Total cost for the request, if available.

    Returns
    -------
    None
        This function commits database updates for messages and pricing.
    """
    await history_manager.save_messages(
        session_id=session_id,
        messages=[
            HumanMessage(content=user_message),
            *tool_messages_from_flat_json(trajectory),
            AIMessage(content=response_text),
        ],
    )
    if request_cost > 0.0:
        await history_manager.increment_session_price(session_id, request_cost)


@router.post("/", response_model=OrchestratorIO, response_model_exclude_none=True)
async def orchestrator_chat(request: OrchestratorIO) -> OrchestratorIO:
    """
    Run the orchestrator in blocking mode.

    Parameters
    ----------
    request : OrchestratorIO
        Input containing session_id and message.

    Returns
    -------
    OrchestratorIO
        Structured response with message and optional attachments.
    """
    try:
        # Load chat history from database (LangChain messages)
        chat_history_langchain = await history_manager.get_messages_for_session(request.session_id)
        chat_history_dicts = langchain_messages_to_dicts(chat_history_langchain)
        chat_history = dict_to_dspy_format(chat_history_dicts)

        with dspy_context() as lm:
            start_time = time.time()
            start_index = len(getattr(lm, "history", []) or [])
            prediction = orchestrator_agent(
                user_message=request.message,
                chat_history=chat_history,
            )
            total_time = time.time() - start_time
            logger.debug(f"Orchestrator response time (non-streaming): {total_time:.4f}s")
            request_cost = extract_request_cost(lm, start_index)

            attachments: List[File] = getattr(prediction, "attachments", None)
            response_text: str = getattr(prediction, "response", "") or ""

        await persist_chat_and_cost(
            session_id=request.session_id,
            user_message=request.message,
            response_text=response_text,
            trajectory=prediction.trajectory,
            request_cost=request_cost,
        )

        return OrchestratorIO(
            session_id=request.session_id,
            message=response_text,
            attachments=[file.to_base64().model_dump() for file in attachments] if attachments else None,
        )
    except Exception as exc:
        logger.error(f"Error in orchestrator_chat: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/stream/")
async def orchestrator_chat_stream(request: OrchestratorIO) -> StreamingResponse:
    """
    Run the orchestrator in streaming mode (SSE).

    Parameters
    ----------
    request : OrchestratorIO
        Input containing session_id and message.

    Returns
    -------
    StreamingResponse
        SSE stream with token events and final OrchestratorIO payload.
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        # Load chat history
        chat_history_langchain = await history_manager.get_messages_for_session(request.session_id)
        chat_history_dicts = langchain_messages_to_dicts(chat_history_langchain)
        chat_history = dict_to_dspy_format(chat_history_dicts)

        try:
            with dspy_context() as lm:
                stream_agent = dspy.streamify(
                    orchestrator_agent,
                    stream_listeners=[
                        dspy.streaming.StreamListener(signature_field_name="response"),
                        dspy.streaming.StreamListener(signature_field_name="reasoning"),
                    ],
                    status_message_provider=OrchestratorStatusProvider(),
                    is_async_program=True,
                )
                final_prediction = None
                start_time = time.time()
                start_index = len(getattr(lm, "history", []) or [])
                first_token_received = False

                async for chunk in stream_agent(user_message=request.message, chat_history=chat_history):
                    if isinstance(chunk, dspy.streaming.StatusMessage):
                        message = chunk.message
                        if hasattr(message, "__await__"):
                            message = await message

                        # Skip empty status messages
                        if not message:
                            continue

                        logger.debug(f"Status message: {message}")
                        status_event = {
                            "type": "intermediate_steps",
                            "status": "success",
                            "session_id": request.session_id,
                            "data": {"status": message},
                        }

                        yield f"data: {json.dumps(status_event)}\n\n"
                    elif isinstance(chunk, dspy.streaming.StreamResponse):
                        if not first_token_received:
                            time_to_first_token = time.time() - start_time
                            logger.debug(f"Time to first token: {time_to_first_token:.4f}s")
                            first_token_received = True

                        token_chunk = chunk.chunk
                        event = {
                            "status": "success",
                            "session_id": request.session_id,
                            "data": {"token": token_chunk},
                        }
                        if chunk.signature_field_name == "reasoning":
                            event["type"] = "reasoning"
                        else:
                            event["type"] = "answer"

                        yield f"data: {json.dumps(event)}\n\n"
                    elif isinstance(chunk, dspy.Prediction):
                        total_time = time.time() - start_time
                        logger.debug(f"Total streaming time: {total_time:.4f}s")
                        final_prediction = chunk
                        # Send completion event
                        event = {
                            "type": "complete",
                            "status": "success",
                            "session_id": request.session_id,
                            "data": {
                                "response": chunk.response,
                            },
                        }
                        if hasattr(chunk, "attachments"):
                            attachments: List[File] = chunk.attachments
                            event["data"]["attachments"] = [file.to_base64().model_dump() for file in attachments]

                        yield f"data: {json.dumps(event)}\n\n"

                if final_prediction is not None:
                    response_text: str = final_prediction.response

                    request_cost = extract_request_cost(lm, start_index)
                    await persist_chat_and_cost(
                        session_id=request.session_id,
                        user_message=request.message,
                        response_text=response_text,
                        trajectory=final_prediction.trajectory,
                        request_cost=request_cost,
                    )
        except Exception as exc:
            logger.error(f"Error in orchestrator_chat_stream: {exc}", exc_info=True)
            error_event = {
                "type": "error",
                "status": "error",
                "session_id": request.session_id,
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
