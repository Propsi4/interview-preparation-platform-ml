"""FastAPI Router for chat history management endpoints."""

# Standart library imports
from typing import List

# Thirdparty imports
from fastapi import APIRouter, HTTPException
from ml.core.logging import logger

# Local imports
from ml.api.schemas import StatusResponseSchema
from ml.conversation_history.manager import ConversationHistoryManager
from ml.conversation_history.schemas import ChatMessageSchema, ChatSessionOverviewSchema, ChatSessionDetailsSchema
from ml.db.engine import connect_to_db
from ml.db.repositories.chat_messages import ChatMessageRepository
from ml.db.repositories.chat_sessions import ChatSessionRepository

router = APIRouter()

history_manager = ConversationHistoryManager()


@router.get("/session/{session_id}")
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
        async with connect_to_db() as session:
            session_repo = ChatSessionRepository(session)
            session_model = await session_repo.get_by_session_id(session_id)
            messages_repo = ChatMessageRepository(session)
            messages = await messages_repo.list_by_session_id(session_id)
            if session_model is None:
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

            return ChatSessionDetailsSchema(
                session_id=session_id,
                title=session_model.title,
                created_at=session_model.created_at,
                updated_at=session_model.updated_at,
                total_messages=len(messages),
                price=session_model.price,
                interview_finished=session_model.interview_finished,
                evaluated=session_model.evaluated,
                search_query_id=session_model.search_query_id,
                messages=[
                    ChatMessageSchema(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        created_at=msg.created_at,
                    )
                    for msg in messages
                ],
            )

    except Exception as e:
        logger.error(f"Error getting messages for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve messages: {str(e)}")


@router.get("/sessions", response_model=List[ChatSessionOverviewSchema])
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


@router.patch("/session/{session_id}/title")
async def rename_chat_session(session_id: str, new_title: str) -> StatusResponseSchema:
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
            return StatusResponseSchema(status="ok", message=f"Session {session_id} renamed to '{new_title}'")
        else:
            return StatusResponseSchema(status="error", message=f"Failed to rename session {session_id}")

    except Exception as e:
        logger.error(f"Error renaming session {session_id}: {e}", exc_info=True)
        return StatusResponseSchema(status="error", message=f"Failed to rename session {session_id}: {str(e)}")


@router.get("/session/{session_id}/price")
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


@router.delete("/session/{session_id}")
async def delete_session_history(session_id: str) -> StatusResponseSchema:
    """
    Delete all messages for a specific session.

    Parameters
    ----------
    session_id : str
        The session identifier.

    Returns
    -------
    StatusResponseSchema
        JSONResponse with success status.
    """
    try:
        logger.info(f"Deleting history for session: {session_id}")

        # Delete session history
        success = await history_manager.delete_chat_by_session_id(session_id)

        if success:
            return StatusResponseSchema(status="ok", message=f"Session {session_id} deleted")
        else:
            return StatusResponseSchema(status="error", message=f"Failed to delete session {session_id}. Not found.")

    except Exception as e:
        logger.error(f"Error deleting history for session {session_id}: {e}", exc_info=True)
        return StatusResponseSchema(status="error", message=f"Failed to delete session {session_id}: {str(e)}")
