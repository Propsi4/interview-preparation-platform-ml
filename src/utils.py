"""Shared utilities for DSPy requests."""

# Thirdparty imports
import dspy
from langchain_core.messages import AIMessage, HumanMessage

# Local imports
from src.conversation_history.manager import ConversationHistoryManager

history_manager = ConversationHistoryManager()


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
    search_query_id: int,
    user_message: str,
    response_text: str,
    request_cost: float,
    interview_finished: bool | None = None,
) -> None:
    """
    Persist chat messages and update session pricing if applicable.

    Parameters
    ----------
    session_id : str
        The chat session identifier.
    search_query_id : int
        Search query identifier associated with the session.
    user_message : str
        Raw user message content.
    response_text : str
        Final assistant response text.
    request_cost : float
        Total cost for the request, if available.
    interview_finished : bool | None
        Whether the interview is finished; when True, it updates the session state.

    Returns
    -------
    None
        This function commits database updates for messages and pricing.
    """
    await history_manager.save_messages(
        session_id=session_id,
        search_query_id=search_query_id,
        messages=[
            HumanMessage(content=user_message),
            AIMessage(content=response_text),
        ],
    )
    if request_cost > 0.0:
        await history_manager.increment_session_price(session_id, request_cost)
    if interview_finished:
        await history_manager.set_interview_finished(session_id, True)
