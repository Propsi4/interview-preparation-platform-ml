"""Agent for aggregating vacancy requirements."""

import dspy
from typing import List


class RequirementsAggregatorSignature(dspy.Signature):
    """
    Signature for aggregating vacancy requirements.

    ### ROLE ###
    You are an expert Technical Recruiter and Job Analyst.
    Your task is to consolidate multiple lists of vacancy requirements into a SINGLE, comprehensive, and deduplicated Master List.

    ### RULES ###
    1. **NO LOSS OF INFORMATION**: Every single distinct skill, tool, or requirement mentioned in the input MUST be represented in the final list.
    2. **INTELLIGENT DEDUPLICATION**:
       - Combine identical or highly similar concepts (e.g., "Python 3.8+", "Python 3.x" -> "Python").
       - Maintain specific levels if they differ significantly, otherwise genericize sensibly (e.g. "English B2", "English C1" -> "English (Intermediate to Advanced)").
       - **Strictly deduplicate**: Do not list "Python" and "Python Language" separately.
    3. **FORMAT**: Return a clean, bulleted list or a comma-separated text that represents individual requirements clearly.
    4. **SCOPE**: Include hard skills, soft skills, languages, and domain knowledge.

    ### INPUT ###
    You will receive `processed_descriptions`, which is a list of requirement strings from various vacancies.

    ### OUTPUT ###
    Produce `aggregated_requirements`: A single string containing the consolidated requirements.
    """

    processed_descriptions: List[str] = dspy.InputField(desc="List of raw requirement strings from vacancies")
    aggregated_requirements: str = dspy.OutputField(desc="Consolidated, deduplicated Master List of requirements")


class RequirementsAggregator(dspy.Module):
    """DSPy module for aggregating requirements."""

    def __init__(self) -> None:
        super().__init__()
        self.prog = dspy.ChainOfThought(RequirementsAggregatorSignature)

    def forward(self, processed_descriptions: List[str]) -> dspy.Prediction:
        """Run the aggregator."""
        return self.prog(processed_descriptions=processed_descriptions)
