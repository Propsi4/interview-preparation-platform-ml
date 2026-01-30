"""DSPy-based extractor for technical requirements from vacancy descriptions."""

# Thirdparty imports
import dspy
from dspy.utils.asyncify import asyncify


class TechnicalRequirementsSignature(dspy.Signature):
    """Extract technical requirements from a vacancy description."""

    vacancy_description: str = dspy.InputField(desc="Full vacancy description")
    processed_description: str = dspy.OutputField(
        desc="Only the technical requirements, concise and structured text."
    )


class TechnicalRequirementsExtractor(dspy.Module):
    """DSPy module that extracts technical requirements."""

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(TechnicalRequirementsSignature)

    def forward(self, vacancy_description: str) -> dspy.Prediction:
        """
        Extract technical requirements from the given description.

        Uses DSPy prompting to transform the input into a concise
        technical requirements-only summary.

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
