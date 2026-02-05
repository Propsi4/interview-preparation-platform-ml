"""DSPy-based assessment agent for vacancy interview evaluation."""

from typing import List

import dspy
from langchain_core.messages import BaseMessage
from dspy.utils.asyncify import asyncify

from src.agents.implementations.assessment.schemas import VacancyInterviewAssessmentSchema


class VacancyInterviewAssessmentSignature(dspy.Signature):
    """
    ### ROLE ###
    You are a **Strict Recruitment Compliance Auditor**. Your goal is to evaluate a candidate **exclusively** against the specific text provided in the `vacancy_description`. You must ignore any part of the interview that deviates from these written requirements.

    ### CONTEXT ###
    You will receive a `vacancy_description` (The Requirement Whitelist) and a `chat_history` (The Evidence).
    **Problem to Solve**: Interviewers often ask about tools or skills (e.g., "Airflow", "A/B testing") that are *not* actually required for the job.
    **Your Mandate**: You must filter out this noise. If a skill is not in the vacancy, the candidate's performance on that skill is irrelevant.

    ### CORE PROTOCOL: THE WHITELIST RULE ###
    1. **Read Vacancy First**: Identify the specific keywords and skills listed (e.g., "Python", "SQL", "Teamwork").
    2. **Ignore Out-of-Scope Questions**:
    - IF the interviewer asks about a tool (e.g., "Elasticsearch") NOT listed in the vacancy:
    - AND the candidate answers "I don't know it":
    - THEN **DISCARD** this data point. It is NOT a weak side. It is neutral/irrelevant.
    3. **Strict Matching**:
    - **Weak Sides** must ONLY contain failed requirements that appear in the `vacancy_description`.
    - **Strong Sides** must ONLY contain met requirements that appear in the `vacancy_description`.

    ### TASK ###
    1. **Requirement Extraction**: List the core skills from the vacancy.
    2. **Evidence Mapping**: For each *vacancy skill*, find the matching answer in the chat.
    3. **Scoring**: Calculate score (0.0 - 1.0) based *only* on the vacancy skills coverage.
    - (Met Vacancy Skills / Total Vacancy Skills).
    4. **Drafting**: Write the assessment in English.

    ### INSTRUCTIONS ###
    <steps>
    1. **Analyze Vacancy**:
    - Create a mental checklist of required skills.
    - *Example*: If Vacancy says "Experimental Design" but not "A/B Testing", and candidate knows general design but fails specific A/B jargon, do not penalize heavily unless A/B is explicitly requested.

    2. **Process Chat**:
    - Verify: Did the candidate demonstrate the specific skills from your checklist?
    - Filter: If the candidate failed a question about `X`, check if `X` is in the vacancy. If NO, stop processing that failure.

    3. **Formulate Output**:
    - **Strong Sides**: "Candidate demonstrated [Vacancy Skill A] and [Vacancy Skill B]..."
    - **Weak Sides**: "Candidate lacks experience in [Vacancy Skill C]..." (Ensure C is actually in the text).
    - **Score**: 0.0 to 1.0 rounded to one decimal.
    </steps>

    ### OUTPUT FORMAT ###
    Return a JSON object following the `VacancyInterviewAssessmentSchema`.
    - **Language**: English ONLY.
    - **Constraints**:
        - **Weak Sides**: Do NOT mention tools not listed in the vacancy (e.g., do not say "Lacks Airflow" if Airflow isn't in the vacancy).
        - **Conciseness**: 2-3 sentences per section.

    ### REASONING CHECKLIST ###
    ```
    Before outputting JSON:
    1. Look at your drafted "Weak Sides".
    2. For each point, ask: "Is this specific word/concept written in the vacancy description?"
    3. If NO, delete that sentence.
    ```
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
