"""DSPy-based extractor for requirements from vacancy descriptions."""

# Thirdparty imports
import dspy
from dspy.utils.asyncify import asyncify


class RequirementsSignature(dspy.Signature):
    """Extract requirements from a vacancy description (including Languages, skills, etc.)."""

    vacancy_description: str = dspy.InputField(desc="Full vacancy description")
    processed_description: str = dspy.OutputField(
        desc="Only the requirements, concise and structured text."
    )


class RequirementsExtractor(dspy.Module):
    """DSPy module that extracts requirements."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(RequirementsSignature)

    def forward(self, vacancy_description: str) -> dspy.Prediction:
        """
        Extract requirements from the given description.

        Uses DSPy prompting to transform the input into a concise
        requirements-only summary.

        Parameters
        ----------
        vacancy_description : str
            Full vacancy description text.

        Returns
        -------
        dspy.Prediction
            Prediction containing processed_description.
        """
        return self.generator(vacancy_description=vacancy_description)

    async def aforward(self, *args, **kwargs) -> dspy.Prediction:
        """
        Async wrapper for the forward method.

        Parameters
        ----------
        *args
            Positional arguments passed to forward.
        **kwargs
            Keyword arguments passed to forward.
        """
        return await asyncify(self.__call__)(*args, **kwargs)
