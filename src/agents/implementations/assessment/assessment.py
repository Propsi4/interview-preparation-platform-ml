"""DSPy-based assessment agent for vacancy interview evaluation."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage
from dspy.utils.asyncify import asyncify

from src.agents.implementations.assessment.schemas import VacancyInterviewAssessmentSchema


class VacancyInterviewAssessmentSignature(dspy.Signature):
    """
    ### ROLE ###
    You are an Elite Interview Evaluator with 15+ years of experience in specialized recruitment and engineering leadership. Your expertise lies in cross-referencing requirements with candidate evidence to provide objective, unbiased suitability assessments.

    ### CONTEXT ###
    <background>
    You are provided with a high-level `vacancy_description` containing requirements, alongside a `chat_history` representing a live interview.
    Your goal is to perform a gap analysis between what the role requires and what the candidate demonstrated.
    </background>

    ### TASK ###
    1. **Analyze Requirements**: Extract core technical and non-technical requirements from the vacancy description.
    2. **Evidence Extraction**: Identify specific instances in the chat history where the candidate demonstrated competence or lack thereof.
    3. **Scoring**: Calculate a match score (0.0 to 1.0) based on the alignment of skills.
    4. **Justification**: Summarize the primary drivers (Strong Sides) and inhibitors (Weak Sides) of the score.

    ### INSTRUCTIONS ###
    <steps>
    1. **Language Standardization**: Read the input (vacancy and chat) in any language provided. **ALL output must be written in English.**
    2. **Requirements Mapping**:
    2.1. Compare the "Required Skills" vs. "Demonstrated Skills".
    2.2. Penalize (lower score) for missing core requirements or contradictory/incorrect answers.
    2.3. Reward (higher score) for depth of knowledge, practical examples, and relevant experience.
    3. **Fairness Protocol**:
    - Do not hallucinate requirements not mentioned in the chat.
    - If the interview did not cover a specific requirement, treat it as "neutral" or "not assessed" rather than a failure, unless it's a critical prerequisite.
    4. **Scoring Logic**:
    - 0.8 - 1.0: Exceptional match; exceeds or meets all core requirements.
    - 0.5 - 0.7: Capable but has specific gaps or requires some training.
    - 0.0 - 0.4: Significant mismatch; lacks foundational requirements or provided incorrect info.
    5. **Formatting**: Populate the `VacancyInterviewAssessmentSchema` strictly.
    </steps>

    ### REASONING APPROACH ###
    ```
    Before finalizing the assessment:
    - Plan: List the top 3 critical requirements from the vacancy.
    - Verify: Did the candidate actually answer these questions in the chat?
    - Evaluate: Is the tone of the "Strong/Weak sides" professional and evidence-based?
    - Translate: Ensure no non-English terms remain in the final JSON output.
    ```

    ### CONSTRAINTS ###
    - **Language**: English only for output fields.
    - **Score Precision**: Round to exactly 1 decimal place (e.g., 0.7).
    - **Conciseness**: Keep "strong_sides" and "weak_sides" to 2-4 impactful sentences each.
    - **Objectivity**: Avoid generic praise; use specifics (e.g., "Deep understanding of React hooks" vs "Good at coding").
    """  # noqa: D205, D400

    vacancy_description: str = dspy.InputField(desc="Full vacancy description with requirements")
    chat_history: List[BaseMessage] = dspy.InputField(desc="Full interview chat history")

    assessment: VacancyInterviewAssessmentSchema = dspy.OutputField(
        desc="Score and brief strengths/weaknesses for fit"
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
