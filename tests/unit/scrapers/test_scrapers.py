"""
Unit tests for the scrapers module.

Verifies page content retrieval, text extraction, URL scraping, and
result aggregation in the DouScraper and its base class ScraperBase.
"""

# Standart library imports
from unittest.mock import AsyncMock, MagicMock, patch

# Thirdparty imports
import pytest
from playwright.async_api import Browser, Locator, Page

# Local imports
from src.scrapers.implementations.dou import DouScraper
from src.scrapers.schemas.vacancy import VacancySchema


class TestDouScraper:
    """Test suite for the DouScraper class."""

    @pytest.mark.asyncio
    async def test_safe_text_success(self) -> None:
        """
        Verify that _safe_text correctly strips and cleans text content from a locator.

        Returns
        -------
        None
        """
        scraper = DouScraper(headless=True)
        mock_locator = MagicMock(spec=Locator)
        mock_locator.text_content = AsyncMock(return_value="  Python\n   Developer\t ")

        cleaned_text = await scraper._safe_text(mock_locator)
        assert cleaned_text == "Python Developer"

    @pytest.mark.asyncio
    async def test_safe_text_exception_returns_none(self) -> None:
        """
        Verify that _safe_text returns None when text extraction raises an error.

        Returns
        -------
        None
        """
        scraper = DouScraper(headless=True)
        mock_locator = MagicMock(spec=Locator)
        mock_locator.text_content = AsyncMock(side_effect=Exception("Playwright error"))

        cleaned_text = await scraper._safe_text(mock_locator)
        assert cleaned_text is None

    @pytest.mark.asyncio
    async def test_extract_total_results(self) -> None:
        """
        Verify that _extract_total_results parses the header text correctly.

        Returns
        -------
        None
        """
        scraper = DouScraper(headless=True)
        mock_page = MagicMock(spec=Page)
        mock_locator = MagicMock(spec=Locator)
        mock_page.locator.return_value = mock_locator

        # Scenario 1: Found digit
        mock_locator.text_content = AsyncMock(return_value="142 vacancies found")
        total = await scraper._extract_total_results(mock_page)
        assert total == 142

        # Scenario 2: No digit found
        mock_locator.text_content = AsyncMock(return_value="No vacancies")
        total_none = await scraper._extract_total_results(mock_page)
        assert total_none is None

    @pytest.mark.asyncio
    async def test_extract_vacancies_urls(self) -> None:
        """
        Verify that _extract_vacancies_urls_from_page extracts list of href strings.

        Returns
        -------
        None
        """
        scraper = DouScraper(headless=True)
        mock_page = MagicMock(spec=Page)
        mock_locator1 = MagicMock(spec=Locator)
        mock_locator1.get_attribute = AsyncMock(return_value="https://jobs.dou.ua/vacancies/1")
        mock_locator2 = MagicMock(spec=Locator)
        mock_locator2.get_attribute = AsyncMock(return_value="https://jobs.dou.ua/vacancies/2")

        mock_container_locator = MagicMock(spec=Locator)
        mock_container_locator.all = AsyncMock(return_value=[mock_locator1, mock_locator2])
        mock_page.locator.return_value = mock_container_locator

        urls = await scraper._extract_vacancies_urls_from_page(mock_page)
        assert list(urls) == ["https://jobs.dou.ua/vacancies/1", "https://jobs.dou.ua/vacancies/2"]

    @pytest.mark.asyncio
    async def test_scrape_vacancy_success(self) -> None:
        """
        Verify that scrape_vacancy correctly navigates and extracts vacancy fields.

        Returns
        -------
        None
        """
        scraper = DouScraper(headless=True)

        mock_page = MagicMock(spec=Page)
        mock_page.goto = AsyncMock()
        mock_page.wait_for_load_state = AsyncMock()

        # Set up safe_text mocking via locator text values
        mock_locator = MagicMock(spec=Locator)
        mock_locator.first = mock_locator
        mock_locator.locator.return_value.first = mock_locator
        mock_locator.text_content = AsyncMock(return_value="Sample Text")
        mock_page.locator.return_value = mock_locator

        # Mock browser and aclose
        mock_browser = MagicMock(spec=Browser)
        mock_browser.new_page = AsyncMock(return_value=mock_page)

        with patch.object(DouScraper, "get_browser", AsyncMock(return_value=mock_browser)), patch.object(
            DouScraper, "aclose", AsyncMock()
        ) as mock_aclose:

            vacancy = await scraper.scrape_vacancy("https://jobs.dou.ua/vacancies/1")

            assert isinstance(vacancy, VacancySchema)
            assert vacancy.title == "Sample Text"
            assert vacancy.company == "Sample Text"
            assert vacancy.url == "https://jobs.dou.ua/vacancies/1"
            mock_aclose.assert_called_once()
