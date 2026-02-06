"""DSPy-based interview agent."""

from typing import List

import dspy
from dspy.utils.asyncify import asyncify
from langchain_core.messages import BaseMessage

from .schemas import InterviewSignature


class InterviewAgent(dspy.Module):
    """DSPy module that produces an interview script."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(InterviewSignature)

    def forward(
        self,
        job_title: str,
        unified_requirements: str,
        chat_history: List[BaseMessage],
        query: str,
    ) -> dspy.Prediction:
        """Run the DSPy predictor."""
        return self.generator(
            job_title=job_title,
            unified_requirements=unified_requirements,
            chat_history=chat_history,
            query=query,
        )

    async def aforward(self, *args, **kwargs) -> dspy.Prediction:
        """
        Async wrapper for the forward method.

        This method wraps the synchronous forward method with asyncify
        to allow asynchronous execution.

        Parameters
        ----------
        *args
            Positional arguments passed to forward.
        **kwargs
            Keyword arguments passed to forward.

        Returns
        -------
        Any
            The result of the forward method.
        """
        return await asyncify(self.__call__)(*args, **kwargs)
