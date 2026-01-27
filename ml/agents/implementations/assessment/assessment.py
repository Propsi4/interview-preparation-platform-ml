"""DSPy-based assessment agent for vacancy interview evaluation."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage
from dspy.utils.asyncify import asyncify

from ml.agents.implementations.assessment.schemas import VacancyInterviewAssessmentSchema


class VacancyInterviewAssessmentSignature(dspy.Signature):
    """Assess candidate interview performance against a vacancy's requirements."""

    vacancy_description: str = dspy.InputField(desc="Full vacancy description with technical requirements")
    chat_history: List[BaseMessage] = dspy.InputField(desc="Full interview chat history")

    assessment: VacancyInterviewAssessmentSchema = dspy.OutputField(
        desc="Score and brief strengths/weaknesses for technical fit"
    )


class VacancyInterviewAssessmentAgent(dspy.Module):
    """DSPy module that scores interview performance against a vacancy."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(VacancyInterviewAssessmentSignature)

    def forward(
        self,
        vacancy_description: str,
        chat_history: List[BaseMessage],
    ) -> dspy.Prediction:
        """Run the DSPy predictor."""
        return self.generator(
            vacancy_description=vacancy_description,
            chat_history=chat_history,
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
