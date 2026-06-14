"""
Unit tests for the requirements extractor pipeline in src/jobs/pipelines/requirements_extractor.py.

Verifies vacancy description requirement extraction logic and configuration passing.
"""

# Standart library imports
from unittest.mock import MagicMock, patch

# Thirdparty imports

# Local imports
from src.jobs.pipelines.requirements_extractor import extract_vacancy_requirements


class TestRequirementsExtractorPipeline:
    """Test suite for the requirements extractor pipeline."""

    def test_extract_vacancy_requirements_empty(self) -> None:
        """
        Verify that extract_vacancy_requirements returns an empty string for empty input.

        Returns
        -------
        None
        """
        res = extract_vacancy_requirements("")
        assert res == ""

    @patch("src.jobs.pipelines.requirements_extractor.RequirementsExtractor")
    @patch("src.jobs.pipelines.requirements_extractor.dspy.LM")
    @patch("src.jobs.pipelines.requirements_extractor.openai_config")
    def test_extract_vacancy_requirements_success(
        self,
        mock_openai_config: MagicMock,
        mock_lm_cls: MagicMock,
        mock_extractor_cls: MagicMock,
    ) -> None:
        """
        Verify that extract_vacancy_requirements correctly initializes the DSPy LM and runs the extractor.

        Parameters
        ----------
        mock_openai_config : MagicMock
            Mock OpenAI configuration settings.
        mock_lm_cls : MagicMock
            Mock DSPy LM class.
        mock_extractor_cls : MagicMock
            Mock RequirementsExtractor class.

        Returns
        -------
        None
        """
        # Configure settings mock
        mock_openai_config.LLM_MODEL = "gpt-4o"
        mock_openai_config.LLM_TEMPERATURE = 0.7
        mock_openai_config.LLM_MAX_TOKENS = 500
        mock_openai_config.ADDITIONAL_LLM_KWARGS = {"top_p": 0.9}

        # Configure extractor prediction
        mock_prediction = MagicMock()
        mock_prediction.processed_description = "  Required: Python, SQL.  "
        mock_extractor = MagicMock()
        mock_extractor.return_value = mock_prediction
        mock_extractor_cls.return_value = mock_extractor

        mock_lm = MagicMock()
        mock_lm_cls.return_value = mock_lm

        res = extract_vacancy_requirements("We need Python developer and SQL expert.")

        assert res == "Required: Python, SQL."
        mock_lm_cls.assert_called_once_with(
            model="gpt-4o",
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
        )
        mock_extractor.assert_called_once_with(vacancy_description="We need Python developer and SQL expert.")
