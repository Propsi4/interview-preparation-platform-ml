"""FastAPI Router for chat history management endpoints."""

# Standart library imports
from typing import List

# Thirdparty imports
from fastapi import APIRouter, HTTPException
from loguru import logger

# Local imports
from ml.conversation_history.manager import ConversationHistoryManager
from ml.conversation_history.schemas import ChatSessionOverviewSchema, ChatSessionDetailsSchema

router = APIRouter()

history_manager = ConversationHistoryManager()


@router.get("/details/{session_id}")
async def get_messages_for_session(session_id: str) -> ChatSessionDetailsSchema:
    """
    Get all messages for a specific chat session.

    Parameters
    ----------
    session_id : str
        The session identifier.

    Returns
    -------
    ChatSessionDetailsSchema
        JSONResponse with messages for the session.
    """
    try:
        logger.info(f"Getting messages for session: {session_id}")

        # Get messages with IDs directly from the manager
        messages_dicts = await history_manager.get_session_history_with_ids(session_id, filter_tool_calls=True)
        session_price = await history_manager.get_session_price(session_id)

        return ChatSessionDetailsSchema(
            session_id=session_id,
            messages=messages_dicts,
            total_messages=len(messages_dicts),
            price=session_price,
        )

    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/list", response_model=List[ChatSessionOverviewSchema])
async def list_chat_sessions() -> List[ChatSessionOverviewSchema]:
    """
    List all chat sessions with basic information.

    Returns
    -------
    List[ChatSessionOverviewSchema]
        List of chat sessions.
    """
    try:
        chat_sessions = await history_manager.get_all_sessions()
        return chat_sessions
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list chat sessions: {str(e)}")


@router.patch("/{session_id}/title")
async def rename_chat_session(session_id: str, new_title: str) -> bool:
    """
    Rename a chat session by its ID.

    Parameters
    ----------
    session_id : str
        The chat session ID to rename.
    new_title : str
        The new title for the chat session.

    Returns
    -------
    bool
        JSONResponse with success status.
    """
    try:
        logger.info(f"Renaming chat session {session_id} to '{new_title}'")

        success = await history_manager.update_session_title(session_id, new_title)

        if success:
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error renaming session {session_id}: {e}", exc_info=True)
        return False


@router.get("/price/{session_id}")
async def get_session_price(session_id: str) -> float:
    """
    Get the total price accumulated for a session.

    Parameters
    ----------
    session_id : str
        The session identifier.

    Returns
    -------
    float
        Session price.
    """
    try:
        price = await history_manager.get_session_price(session_id)
        return price
    except Exception as e:
        logger.error(f"Error retrieving price for session {session_id}: {e}", exc_info=True)
        return 0.0


@router.delete("/{session_id}")
async def delete_session_history(session_id: str) -> bool:
    """
    Delete all messages for a specific session.

    Parameters
    ----------
    session_id : str
        The session identifier.

    Returns
    -------
    bool
        JSONResponse with success status.
    """
    try:
        logger.info(f"Deleting history for session: {session_id}")

        # Delete session history
        success = await history_manager.delete_chat_by_session_id(session_id)

        if success:
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error deleting history for session {session_id}: {e}", exc_info=True)
        return False
