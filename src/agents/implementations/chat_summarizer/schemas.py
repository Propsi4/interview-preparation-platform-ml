"""Schemas for chat summarization agent."""

import dspy
from typing import List
from langchain_core.messages import BaseMessage


class ChatSummarizationSignature(dspy.Signature):
    """
    ### ROLE ###
    You are an expert technical interviewer assistant. Your goal is to summarize the early part of a conversation history to reduce its token footprint while STRICTLY preserving all context critical for the technical assessment logic.

    ### CRITICAL CONTEXT TO PRESERVE ###
    The downstream agent uses a 3-strike rule to assess technical topics. You MUST preserve:
    1. **Language**: The user's preferred language (e.g., English, Spanish).
    2. **Topics Status**: For each technical requirement discussed:
        - Was it **fully answered** (passed)?
        - Was it **failed** (can't answer)?
        - Is it **currently active** (pending)?
    3. **Identified Gaps**: If the user's answer was vague or incomplete, what SPECIFICALLY was missing? (e.g., "User mentioned SQL but not NoSQL").

    ### INSTRUCTIONS ###
    - Output a single summary string.
    - The summary should be written as a narrative or structured notes that the system can read as "Previous Context".
    """  # noqa: D205, D400

    messages: List[BaseMessage] = dspy.InputField(desc="The list of chat messages to summarize (serialized to string).")
    summary: str = dspy.OutputField(desc="A concise summary strictly preserving the critical context points.")
