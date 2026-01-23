"""ConversationHistoryManager for managing chat history operations.

This module provides a SQLAlchemy ORM-based chat history manager
that works with LangChain message types.
"""

# Standart library imports
from typing import List

# Thirdparty imports
from langchain_core.messages import BaseMessage, HumanMessage
from loguru import logger
from sqlalchemy import select, func

# Local folder imports
from ml.db.engine import connect_to_db
from ml.db.models.chat_session import ChatSession
from ml.db.models.chat_message import ChatMessage
from .utils import dicts_to_langchain_messages
from .schemas import ChatSessionsOverview, ChatMessage as ChatMessageSchema


class ConversationHistoryManager:
    """Manager for conversation history operations using SQLAlchemy ORM."""

    async def get_messages_for_session(self, session_id: str) -> List[BaseMessage]:
        """
        Retrieve all messages for a provided session as LangChain messages.

        Parameters
        ----------
        session_id : str
            The session ID to retrieve messages for.

        Returns
        -------
        List[BaseMessage]
            List of LangChain message objects (HumanMessage, AIMessage, ToolMessage).

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> messages = await manager.get_messages_for_session("session123")
        >>> # Returns: [HumanMessage(content="Hello"), AIMessage(content="Hi"), ...]
        """
        try:
            logger.info(f"Retrieving messages for chat session: {session_id}")

            async with connect_to_db() as session:
                query = (
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                result = await session.execute(query)
                messages = result.scalars().all()

                # Convert to dictionaries then to LangChain messages
                message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
                langchain_messages = dicts_to_langchain_messages(message_dicts)

                logger.info(f"Retrieved {len(langchain_messages)} messages for chat session: {session_id}")
                return langchain_messages

        except Exception as e:
            logger.error(f"Error retrieving messages for chat session {session_id}: {e}")
            raise

    async def get_session_history_with_ids(
        self, session_id: str, filter_tool_calls: bool = False
    ) -> List[ChatMessageSchema]:
        """
        Retrieve all messages for a provided chat session as dictionaries including IDs.

        Parameters
        ----------
        session_id : str
            The chat session ID to retrieve messages for.
        filter_tool_calls : bool, optional
            Whether to filter out tool messages. Default is False.

        Returns
        -------
        List[ChatMessageSchema]
            List of dictionaries containing message data (id, role, content, created_at).

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> messages = await manager.get_session_history_with_ids("session123")
        >>> # Returns: [ChatMessage(id=1, role="user", content="Hello", created_at=datetime.datetime(2021, 1, 1, 0, 0, 0)), ...]
        """
        try:
            logger.info(f"Retrieving messages with IDs for chat session: {session_id}")

            async with connect_to_db() as session:
                query = (
                    select(ChatMessage)
                    .filter(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at.asc())
                )
                result = await session.execute(query)
                messages = result.scalars().all()

                if filter_tool_calls:
                    messages = [msg for msg in messages if msg.role != "tool"]

                messages = [
                    ChatMessageSchema(
                        id=msg.id,
                        role=msg.role,
                        content=msg.content,
                        created_at=msg.created_at,
                    )
                    for msg in messages
                ]

                logger.info(f"Retrieved {len(messages)} messages for chat session: {session_id}")
                return messages

        except Exception as e:
            logger.error(f"Error retrieving messages with IDs for chat session {session_id}: {e}")
            raise

    async def get_all_sessions(self) -> List[ChatSessionsOverview]:
        """
        Retrieve all chat sessions with basic information.

        Returns
        -------
        List[ChatSessionsOverview]
            List of chat sessions with basic information.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> sessions = await manager.get_all_sessions()
        >>> # Returns: [ChatSessionsOverview(session_id="chat_session_123", title="Hello", created_at=datetime.datetime(2021, 1, 1, 0, 0, 0), updated_at=datetime.datetime(2021, 1, 1, 0, 0, 0), message_count=10, price=10.0), ...]
        """
        try:
            async with connect_to_db() as session:
                query = (
                    select(ChatSession)
                    .order_by(ChatSession.updated_at.desc())
                )
                result = await session.execute(query)
                chat_sessions = result.scalars().all()
                chat_sessions_info: List[ChatSessionsOverview] = []

                for chat_session in chat_sessions:
                    count_query = select(func.count()).select_from(ChatMessage).filter(ChatMessage.session_id == chat_session.session_id)
                    count_result = await session.execute(count_query)
                    message_count = count_result.scalar_one_or_none()
                    chat_sessions_info.append(
                        ChatSessionsOverview(
                            session_id=chat_session.session_id,
                            title=chat_session.title,
                            created_at=chat_session.created_at,
                            updated_at=chat_session.updated_at,
                            message_count=message_count,
                            price=chat_session.price,
                        )
                    )

                return chat_sessions_info
        except Exception as e:
            logger.error(f"Error retrieving sessions: {e}")
            raise

    async def get_session_price(self, session_id: str) -> float:
        """
        Get the current total price for a chat session.

        Parameters
        ----------
        session_id : str
            The chat session ID to look up.

        Returns
        -------
        float
            The total accumulated price for the chat session.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> total = await manager.get_session_price("chat_session_123")
        """
        try:
            async with connect_to_db() as session:
                query = select(ChatSession).filter(ChatSession.session_id == session_id)
                result = await session.execute(query)
                chat_session = result.scalar_one_or_none()
                if chat_session is None:
                    return 0.0
                return chat_session.price
        except Exception as e:
            logger.error(f"Error retrieving chat session price for {session_id}: {e}")
            raise

    async def increment_session_price(self, session_id: str, price_delta: float) -> float:
        """
        Increment the total price for a chat session.

        Parameters
        ----------
        session_id : str
            The chat session ID to update.
        price_delta : float
            The incremental price to add to the session total.

        Returns
        -------
        float
            The updated total price for the chat session.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> total = await manager.increment_session_price("chat_session_123", 0.01)
        """
        try:
            async with connect_to_db() as session:
                try:
                    query = select(ChatSession).filter(ChatSession.session_id == session_id)
                    result = await session.execute(query)
                    chat_session = result.scalar_one_or_none()
                    if chat_session is None:
                        chat_session = ChatSession(session_id=session_id, price=0.0)
                        session.add(chat_session)
                        await session.flush()

                    chat_session.price = chat_session.price + price_delta
                    await session.commit()
                    return chat_session.price
                except Exception:
                    await session.rollback()
                    raise
        except Exception as e:
            logger.error(f"Error incrementing chat session price for {session_id}: {e}")
            raise

    async def save_messages(self, session_id: str, messages: List[BaseMessage]) -> None:
        """
        Save a list of LangChain messages for a chat session.

        Parameters
        ----------
        session_id : str
            The chat session ID to save messages for.
        messages : List[BaseMessage]
            List of LangChain message objects to save.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> await manager.save_messages(
        ...     "chat_session_123",
        ...     [HumanMessage(content="Hello"), AIMessage(content="Hi")]
        ... )
        """
        try:
            logger.info(f"Saving {len(messages)} messages for chat session: {session_id}")

            async with connect_to_db() as session:
                try:
                    # Ensure session exists (create if not exists)
                    query = select(ChatSession).filter(ChatSession.session_id == session_id)
                    result = await session.execute(query)
                    chat_session = result.scalar_one_or_none()

                    if not chat_session:
                        # Get first user message for title if session doesn't exist
                        first_user_msg = next((msg for msg in messages if isinstance(msg, HumanMessage)), None)
                        title = first_user_msg.content[:100] if first_user_msg else None
                        chat_session = ChatSession(
                            session_id=session_id,
                            title=title,
                        )
                        session.add(chat_session)

                    # Save all messages
                    chat_messages = [ChatMessage(
                        session_id=session_id,
                        role=msg.role,
                        content=msg.content,
                    ) for msg in messages]
                    session.add_all(chat_messages)

                    await session.commit()
                    logger.info(f"Successfully saved {len(messages)} messages for chat session: {session_id}")
                except Exception:
                    await session.rollback()
                    raise

        except Exception as e:
            logger.error(f"Error saving messages for chat session {session_id}: {e}")
            raise

    async def update_session_title(self, session_id: str, new_title: str) -> bool:
        """
        Update the title of a chat session by its ID.

        Parameters
        ----------
        session_id : str
            The chat session ID to update.
        new_title : str
            The new title for the session.

        Returns
        -------
        bool
            True if update was successful, False otherwise.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> success = await manager.update_session_title("chat_session_123", "New Title")
        """
        try:
            logger.info(f"Updating title for chat session: {session_id} to '{new_title}'")

            async with connect_to_db() as session:
                try:
                    query = select(ChatSession).filter(ChatSession.session_id == session_id)
                    result = await session.execute(query)
                    chat_session = result.scalar_one_or_none()
                    if chat_session:
                        chat_session.title = new_title
                        await session.commit()
                        logger.info(f"Successfully updated title for chat session: {session_id}")
                        return True
                    logger.warning(f"Session {session_id} not found for title update")
                    return False
                except Exception:
                    await session.rollback()
                    raise

        except Exception as e:
            logger.error(f"Error updating chat session title by ID for {session_id}: {e}")
            raise

    async def delete_chat_by_session_id(self, session_id: str) -> bool:
        """
        Delete all messages for a chat session by its ID.

        Parameters
        ----------
        session_id : str
            The chat session ID to delete.

        Returns
        -------
        bool
            True if deletion was successful, False otherwise.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> success = await manager.delete_chat_by_session_id("chat_session_123")
        """
        try:
            logger.info(f"Deleting chat for chat session: {session_id}")

            async with connect_to_db() as session:
                try:
                    # Delete session (cascade will handle messages due to relationship)
                    query = select(ChatSession).filter(ChatSession.session_id == session_id)
                    result = await session.execute(query)
                    chat_session = result.scalar_one_or_none()
                    if chat_session:
                        await session.delete(chat_session)
                        await session.commit()
                        logger.info(f"Successfully deleted chat for chat session: {session_id}")
                        return True
                    return False
                except Exception:
                    await session.rollback()
                    raise

        except Exception as e:
            logger.error(f"Error deleting chat for chat session {session_id}: {e}")
            return False

    async def check_health(self) -> bool:
        """
        Check if the database connection is healthy by executing a simple query.

        Returns
        -------
        bool
            True if database connection is healthy, False otherwise.

        Examples
        --------
        >>> manager = ConversationHistoryManager()
        >>> is_healthy = await manager.check_health()
        """
        try:
            async with connect_to_db() as session:
                result = await session.execute(select(1))
                result.scalar_one()
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
