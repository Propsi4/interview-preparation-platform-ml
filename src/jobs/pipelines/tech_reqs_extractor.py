"""Pipeline for extracting technical requirements from vacancy descriptions."""

from src.config.openai import openai_config
from src.agents.implementations.tech_requirements_extractor.extractor import TechnicalRequirementsExtractor
import dspy


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
