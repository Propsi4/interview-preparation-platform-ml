"""DSPy-based technical interview agent."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage
from sqlalchemy import select

from ml.db.engine import connect_to_db
from ml.db.models.vacancies import VacancyModel
from ml.agents.implementations.technical_interview.schemas import InterviewTurnRequestSchema, TechnicalInterviewResponseSchema


class TechnicalInterviewSignature(dspy.Signature):
    """Generate a strict, fair technical interview from role requirements."""

    vacancy_descriptions: List[str] = dspy.InputField(desc="Vacancy descriptions")
    chat_history: List[BaseMessage] = dspy.InputField(desc="Conversation history between interviewer and candidate")
    query: str = dspy.InputField(desc="Latest user input")

    response: TechnicalInterviewResponseSchema = dspy.OutputField(desc="Technical question or final technical summary. No soft skills.")


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


async def run_interview(request: InterviewTurnRequestSchema) -> TechnicalInterviewResponseSchema:
    """Run a technical interview turn using stored vacancy descriptions.

    Parameters
    ----------
    request : InterviewTurnRequestSchema
        Interview input data.

    Returns
    -------
    TechnicalInterviewResponseSchema
        Interview response and completion flag.
    """
    descriptions = await _load_descriptions(request.search_query_id)
    agent = TechnicalInterviewAgent()
    prediction = agent(
        vacancy_descriptions=descriptions,
        chat_history=request.chat_history,
        query=request.query,
    )
    return TechnicalInterviewResponseSchema(
        interview_finished=prediction.interview_finished,
        response=prediction.response,
    )


async def _load_descriptions(search_query_id: int) -> List[str]:
    """Load vacancy descriptions for a search query.

    Parameters
    ----------
    search_query_id : int
        Search query identifier.

    Returns
    -------
    List[str]
        Collected vacancy descriptions.
    """
    async with connect_to_db() as session:
        result = await session.execute(select(VacancyModel).where(VacancyModel.search_query_id == search_query_id))
        vacancies = result.scalars().all()
        return [vacancy.description for vacancy in vacancies if vacancy.description is not None]
