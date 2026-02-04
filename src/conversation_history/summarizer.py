"""Chat history summarizer based on DSPy."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage

from src.config.openai import openai_config
from src.core.logging import logger


class ChatSummarizationSignature(dspy.Signature):
    """
    ### ROLE ###
    You are an expert technical interviewer assistant. Your goal is to summarize the early part of a conversation history to reduce its token footprint while STRICTLY preserving all context critical for the technical assessment logic.

    ### CRITICAL CONTEXT TO PRESERVE ###
    The downstream agent uses a 3-strike rule to assess technical topics. You MUST preserve:
    1. **Language**: The user's preferred language (e.g., English, Spanish).
    2. **Topic Status**: For each technical requirement discussed:
        - Was it **fully answered** (passed)?
        - Was it **failed** (can't answer)?
        - Is it **currently active** (pending)?
    3. **Attempt Counter**: How many times has the interviewer asked about the CURRENT topic? (e.g., "Ask 1", "Retry 1", "Retry 2"). This is vital for the 3-strike logic.
    4. **Identified Gaps**: If the user's answer was vague or incomplete, what SPECIFICALLY was missing? (e.g., "User mentioned SQL but not NoSQL").

    ### INSTRUCTIONS ###
    - Output a single summary string.
    - Do NOT summarize the entire history if it's not provided; only summarize the input `messages`.
    - The summary should be written as a narrative or structured notes that the system can read as "Previous Context".
    """  # noqa: D205, D400

    messages: str = dspy.InputField(desc="The list of chat messages to summarize (serialized to string).")
    summary: str = dspy.OutputField(desc="A concise summary strictly preserving the critical context points.")


class ChatHistorySummarizer:
    """Summarizes chat history to reduce token usage."""

    def __init__(self, max_history_len: int = 10, summary_window: int = 5):
        """
        Initialize the summarizer.

        Parameters
        ----------
        max_history_len : int
             The threshold count of messages. If total messages > max_history_len, summarization triggers.
        summary_window : int
             How many of the *oldest* messages to roll into the summary.
             The most recent (total - summary_window) messages are kept raw.
        """
        self.max_history_len = max_history_len
        self.summary_window = summary_window
        self.lm = dspy.LM(
            model=openai_config.LLM_MODEL,
            temperature=0.0,  # Deterministic for summarization
        )
        self.generator = dspy.ChainOfThought(ChatSummarizationSignature)

    def _serialize_messages(self, messages: List[BaseMessage]) -> str:
        """Convert messages to a string format for the model."""
        buffer = []
        for msg in messages:
            role = "Interviewer" if isinstance(msg, AIMessage) else "Candidate"
            if isinstance(msg, SystemMessage):
                role = "System"
            buffer.append(f"{role}: {msg.content}")
        return "\n".join(buffer)

    def summarize(self, history: List[BaseMessage]) -> List[BaseMessage]:
        """
        Summarize the history if it exceeds the threshold.

        Parameters
        ----------
        history : List[BaseMessage]
            The full conversation history.

        Returns
        -------
        List[BaseMessage]
            The new history starting with a SystemMessage (summary) followed by recent raw messages.
        """
        if len(history) <= self.max_history_len:
            return history

        # Determine split index
        # We want to keep the most recent N messages, where N = len(history) - summary_window
        # Strategy:
        # If len > max_history_len (e.g., 20)
        # Summarize the first (len - keep_recent) messages.
        # Keep the last `keep_recent` messages raw.
        keep_recent_count = min(len(history), self.max_history_len)
        cutoff_index = len(history) - keep_recent_count

        if cutoff_index <= 0:
            return history

        to_summarize = history[:cutoff_index]
        recent_messages = history[cutoff_index:]

        # If existing history already has a summary (SystemMessage at index 0), include it in the input to be merged?
        # Yes, we should serialize it.

        serialized_context = self._serialize_messages(to_summarize)

        logger.info(f"Summarizing {len(to_summarize)} old messages. Keeping {len(recent_messages)} recent ones.")

        with dspy.context(lm=self.lm):
            prediction = self.generator(messages=serialized_context)

        summary_text = getattr(prediction, "summary", "")
        if not summary_text:
            logger.warning("Summarization failed to produce text. Returning original history.")
            return history

        summary_message = SystemMessage(content=f"[PREVIOUS CONTEXT SUMMARY]: {summary_text}")

        return [summary_message] + recent_messages
