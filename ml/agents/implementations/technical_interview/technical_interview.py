"""DSPy-based technical interview agent."""

from typing import List

import dspy
from dspy.utils.asyncify import asyncify
from langchain_core.messages import BaseMessage
from ml.agents.implementations.technical_interview.schemas import TechnicalInterviewResponseSchema


class TechnicalInterviewSignature(dspy.Signature):
    """Generate a strict, fair technical interview from role requirements."""

    vacancy_descriptions: List[str] = dspy.InputField(desc="Vacancy descriptions")
    chat_history: List[BaseMessage] = dspy.InputField(desc="Conversation history between interviewer and candidate")
    query: str = dspy.InputField(desc="Latest user input")

    response: TechnicalInterviewResponseSchema = dspy.OutputField(
        desc="Technical question or final technical summary. No soft skills."
    )


class TechnicalInterviewAgent(dspy.Module):
    """DSPy module that produces a technical interview script."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(TechnicalInterviewSignature)

    def forward(
        self,
        vacancy_descriptions: List[str],
        chat_history: List[BaseMessage],
        query: str,
    ) -> dspy.Prediction:
        """Run the DSPy predictor."""
        return self.generator(
            vacancy_descriptions=vacancy_descriptions,
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
