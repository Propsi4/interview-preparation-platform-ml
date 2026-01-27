"""DSPy-based extractor for technical requirements from vacancy descriptions."""

# Thirdparty imports
import dspy
from dspy.utils.asyncify import asyncify

# Local imports
from ml.config.openai import openai_config


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
        return await asyncify(self.forward)(*args, **kwargs)


def extract_technical_requirements(vacancy_description: str) -> str:
    """
    Extract technical requirements from a vacancy description.

    Creates a DSPy module configured with the current LLM settings
    and returns a cleaned summary of technical requirements.

    Parameters
    ----------
    vacancy_description : str
        Full vacancy description text.

    Returns
    -------
    str
        Processed description containing only technical requirements.
    """
    if not vacancy_description:
        return ""

    lm_kwargs: dict = {}
    if openai_config.LLM_MAX_TOKENS is not None:
        lm_kwargs["max_tokens"] = openai_config.LLM_MAX_TOKENS
    if openai_config.ADDITIONAL_LLM_KWARGS:
        lm_kwargs.update(openai_config.ADDITIONAL_LLM_KWARGS)

    lm = dspy.LM(
        model=openai_config.LLM_MODEL,
        temperature=openai_config.LLM_TEMPERATURE,
        **lm_kwargs,
    )

    extractor = TechnicalRequirementsExtractor()
    with dspy.context(lm=lm):
        prediction = extractor(vacancy_description=vacancy_description)

    processed = getattr(prediction, "processed_description", "") or ""
    return processed.strip()
