"""Chat history summarizer based on DSPy."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage, SystemMessage
from src.agents.implementations.chat_summarizer.schemas import ChatSummarizationSignature
from src.core.logging import logger


class ChatHistorySummarizer(dspy.Module):
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
        self.generator = dspy.ChainOfThought(ChatSummarizationSignature)

    def forward(self, messages: List[BaseMessage]) -> dspy.Prediction:
        """
        Forward pass for the summarizer.

        Parameters
        ----------
        messages : List[BaseMessage]
            The full conversation history.

        Returns
        -------
        List[BaseMessage]
            The new history starting with a SystemMessage (summary) followed by recent raw messages.
        """
        return self.generator(messages=messages)

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

        # Ensure the batch to summarize ends with a human message to avoid splitting QA pairs
        # (e.g., AI question summarized, Human answer raw -> AI loses context of what question it asked)
        while to_summarize and to_summarize[-1].type != "human" and recent_messages:
            to_summarize.append(recent_messages.pop(0))

        logger.info(f"Summarizing {len(to_summarize)} old messages. Keeping {len(recent_messages)} recent ones.")

        prediction = self.__call__(messages=to_summarize)

        summary_text = getattr(prediction, "summary", "")
        if not summary_text:
            logger.warning("Summarization failed to produce text. Returning original history.")
            return history

        summary_message = SystemMessage(content=f"[PREVIOUS CONTEXT SUMMARY]: {summary_text}")

        return [summary_message] + recent_messages
