"""
Unit tests for the DSPy-based AI agents.

Verifies that RequirementsExtractor, RequirementsAggregator, VacancyInterviewAssessmentAgent,
InterviewAgent, and ChatHistorySummarizer invoke their underlying prediction pipelines
correctly, and validates the summarizer's window splitting and QA-pair preservation algorithms.
"""

# Standart library imports
from unittest.mock import MagicMock, patch

# Thirdparty imports
import dspy  # type: ignore[import-untyped]
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

# Local imports
from src.agents.implementations.assessment.assessment import VacancyInterviewAssessmentAgent
from src.agents.implementations.assessment.schemas import VacancyInterviewAssessmentSchema
from src.agents.implementations.chat_summarizer.summarizer import ChatHistorySummarizer
from src.agents.implementations.interview.interview import InterviewAgent
from src.agents.implementations.requirements_aggregator.aggregator import RequirementsAggregator
from src.agents.implementations.requirements_extractor.extractor import RequirementsExtractor


class TestAgentsInitializationAndForward:
    """Test suite for agent pipeline construction and execution."""

    @patch("src.agents.implementations.requirements_extractor.extractor.dspy.ChainOfThought")
    def test_requirements_extractor(self, mock_cot_cls: MagicMock) -> None:
        """
        Verify forward call of RequirementsExtractor invokes the generator.

        Returns
        -------
        None
        """
        mock_generator = mock_cot_cls.return_value
        mock_prediction = MagicMock(spec=dspy.Prediction)
        mock_prediction.processed_description = "Extracted requirements"
        mock_generator.return_value = mock_prediction

        extractor = RequirementsExtractor()
        prediction = extractor.forward(vacancy_description="Looking for Python dev.")

        assert prediction.processed_description == "Extracted requirements"
        mock_generator.assert_called_once_with(vacancy_description="Looking for Python dev.")

    @patch("src.agents.implementations.requirements_aggregator.aggregator.dspy.ChainOfThought")
    def test_requirements_aggregator(self, mock_cot_cls: MagicMock) -> None:
        """
        Verify forward call of RequirementsAggregator invokes the generator.

        Returns
        -------
        None
        """
        mock_generator = mock_cot_cls.return_value
        mock_prediction = MagicMock(spec=dspy.Prediction)
        mock_prediction.aggregated_requirements = "Consolidated skills"
        mock_generator.return_value = mock_prediction

        aggregator = RequirementsAggregator()
        prediction = aggregator.forward(processed_descriptions=["Python", "SQL"])

        assert prediction.aggregated_requirements == "Consolidated skills"
        mock_generator.assert_called_once_with(processed_descriptions=["Python", "SQL"])

    @patch("src.agents.implementations.assessment.assessment.dspy.ChainOfThought")
    def test_assessment_agent(self, mock_cot_cls: MagicMock) -> None:
        """
        Verify forward call of VacancyInterviewAssessmentAgent invokes the generator.

        Returns
        -------
        None
        """
        mock_generator = mock_cot_cls.return_value
        mock_prediction = MagicMock(spec=dspy.Prediction)
        mock_schema = MagicMock(spec=VacancyInterviewAssessmentSchema)
        mock_prediction.assessment = mock_schema
        mock_generator.return_value = mock_prediction

        agent = VacancyInterviewAssessmentAgent()
        prediction = agent.forward(vacancy_description="Required Python.", chat_history=[])

        assert prediction.assessment == mock_schema
        mock_generator.assert_called_once_with(vacancy_description="Required Python.", chat_history=[])

    @patch("src.agents.implementations.interview.interview.dspy.ChainOfThought")
    def test_interview_agent(self, mock_cot_cls: MagicMock) -> None:
        """
        Verify forward call of InterviewAgent invokes the generator.

        Returns
        -------
        None
        """
        mock_generator = mock_cot_cls.return_value
        mock_prediction = MagicMock(spec=dspy.Prediction)
        mock_generator.return_value = mock_prediction

        agent = InterviewAgent()
        prediction = agent.forward(
            job_title="Engineer",
            unified_requirements="Python",
            chat_history=[],
            query="question",
        )

        assert prediction == mock_prediction
        mock_generator.assert_called_once_with(
            job_title="Engineer",
            unified_requirements="Python",
            chat_history=[],
            query="question",
        )


class TestChatHistorySummarizer:
    """Test suite for the ChatHistorySummarizer class and its custom summarization rules."""

    def test_summarize_under_threshold(self) -> None:
        """
        Verify that history is returned untouched if it is below max_history_len.

        Returns
        -------
        None
        """
        summarizer = ChatHistorySummarizer(max_history_len=5, summary_window=2)
        history: list[BaseMessage] = [HumanMessage(content="msg")] * 3
        # Assert history remains unchanged
        assert summarizer.summarize(history) == history

    @patch("src.agents.implementations.chat_summarizer.summarizer.dspy.ChainOfThought")
    def test_summarize_exceeding_threshold(self, mock_cot_cls: MagicMock) -> None:
        """
        Verify history window slicing and QA-pair preservation.

        Returns
        -------
        None
        """
        mock_generator = mock_cot_cls.return_value
        mock_prediction = MagicMock()
        mock_prediction.summary = "A compressed summary of past topics."
        mock_generator.return_value = mock_prediction

        # Set up a summarizer with max_history_len=4
        # We will feed 6 messages:
        # 0: Human ("Start")
        # 1: AI ("Q1")
        # 2: Human ("A1")
        # 3: AI ("Q2")
        # 4: Human ("A2")
        # 5: AI ("Q3")
        history: list[BaseMessage] = [
            HumanMessage(content="Start"),
            AIMessage(content="Q1"),
            HumanMessage(content="A1"),
            AIMessage(content="Q2"),
            HumanMessage(content="A2"),
            AIMessage(content="Q3"),
        ]

        summarizer = ChatHistorySummarizer(max_history_len=4, summary_window=2)

        # Let's call summarize
        summarized_history = summarizer.summarize(history)

        # The cutoff index is len(history) - max_history_len = 6 - 4 = 2.
        # So to_summarize starts as history[:2] (Start, Q1).
        # But wait! to_summarize[-1] is Q1 (type AI/assistant).
        # The while loop pops messages from recent_messages (A1, Q2, A2, Q3) to to_summarize
        # until to_summarize[-1] is of type "human" (HumanMessage).
        # First iteration: A1 is popped. to_summarize[-1] becomes A1 (HumanMessage). Loop terminates!
        # So to_summarize becomes [Start, Q1, A1].
        # recent_messages becomes [Q2, A2, Q3].
        # Let's verify that the mocked generator was called with [Start, Q1, A1].
        mock_generator.assert_called_once_with(messages=history[:3])

        # Verify that output list starts with a SystemMessage representing the summary
        # followed by the remaining recent messages [Q2, A2, Q3]
        assert len(summarized_history) == 4
        assert summarized_history[0].type == "system"
        assert "A compressed summary of past topics" in summarized_history[0].content
        assert summarized_history[1] == history[3]  # Q2
        assert summarized_history[2] == history[4]  # A2
        assert summarized_history[3] == history[5]  # Q3
