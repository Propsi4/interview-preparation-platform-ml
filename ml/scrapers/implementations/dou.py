"""Async scraper for dou.ua vacancies.

Examples
--------
>>> import asyncio
>>> from ml.scrapers.dou import DouScraper
>>> asyncio.run(DouScraper().async_run("HR"))
"""
import asyncio
import re
from typing import Iterable

from playwright.async_api import Locator, Page
from pydantic import PrivateAttr
from ml.scrapers.schemas.vacancy import VacanciesOverviewSchema, VacancySchema
from ml.scrapers.base import ScraperBase
from ml.core.logging import logger


class DouScraper(ScraperBase):
    """Scraper for dou.ua vacancies using Playwright."""

    source_name: str = "dou.ua"
    _base_url: str = PrivateAttr(default="https://jobs.dou.ua/vacancies/")

    async def _open_vacancies_page(self, query: str) -> Page:
        """Open the vacancies page for a query."""
        browser = await self.get_browser()
        page = await browser.new_page()
        await page.goto(f"{self._base_url}?search={query}")
        return page

    async def _extract_total_results(self, page: Page) -> int | None:
        """Extract total results count from the page."""
        total_results = await self._safe_text(page.locator(".b-inner-page-header"))
        # extract all the continuous numbers from the beginning of the string
        match = re.search(r"\d+", total_results)
        if match:
            return int(match.group(0))
        return None

    async def _expand_vacancies_list_page(self, page: Page) -> Page:
        """Clicks 'Load more' button until all vacancies are loaded."""
        while True:
            load_more_container = page.locator('//*[@id="vacancyListId"]/div').first
            a_tag = load_more_container.locator("a").first
            selector = ".more-btn a"
            try:
                await page.wait_for_selector(selector)
            except Exception:
                break

            # Execute the jQuery script inside the browser
            await page.evaluate(f"""
                var $btn = $('{selector}');
                $btn.trigger('mousedown');
                $btn.trigger('mouseup');
                $btn.trigger('click');
            """)
            if await a_tag.get_attribute("style") == "display: none;":
                break
        await page.wait_for_load_state("domcontentloaded")
        return page

    async def _extract_vacancies_urls_from_page(self, page: Page) -> Iterable[str]:
        """Extract vacancies URLs from the page."""
        locators = await page.locator("a.vt").all()
        return [await locator.get_attribute("href") for locator in locators]

    async def scrape_vacancy(self, url: str) -> VacancySchema:
        """Extract vacancy data from the page."""
        browser = await self.get_browser()
        page = await browser.new_page()
        try:
            await page.goto(url)
            await page.wait_for_load_state("domcontentloaded")

            title_coro = self._safe_text(page.locator("h1, .g-h2, h2").first)
            company_coro = page.locator(".info, .l-n").first
            company_name_coro = self._safe_text(company_coro.locator("a").first)
            location_coro = self._safe_text(page.locator(".place, .location, .city").first)
            description_coro = self._safe_text(
                page.locator(".b-typo, .vacancy-section").first
            )

            # Run all extraction coroutines in parallel for better performance
            title, company, location, description = await asyncio.gather(
                title_coro, company_name_coro, location_coro, description_coro
            )

            return VacancySchema(
                title=title,
                company=company,
                location=location,
                description=description,
                url=url,
            )
        finally:
            await self.aclose()

    async def _safe_text(self, locator: Locator) -> str | None:
        """
        Safely read text content from a locator.

        Parameters
        ----------
        locator : Page
            Playwright locator instance.

        Returns
        -------
        str | None
            Stripped text if available.
        """
        try:
            text = await locator.text_content()
            # Remove special characters like \n, \t, \r, etc.
            text: str = re.sub(r'\s+', ' ', text)
            return text.strip()
        except Exception:
            return None

    async def arun(self, query: str) -> VacanciesOverviewSchema:
        """
        Scrape vacancies for a query.

        Parameters
        ----------
        query : str
            Search query to submit on dou.ua (e.g., "HR").
        """
        try:
            page = await self._open_vacancies_page(query)
            total_results = await self._extract_total_results(page)
            logger.info(f"Scraped {total_results} vacancies for query: {query}")
            await self._expand_vacancies_list_page(page)
            vacancies_urls = await self._extract_vacancies_urls_from_page(page)
            return VacanciesOverviewSchema(query=query, total_results=total_results, vacancies_urls=vacancies_urls)
        finally:
            await self.aclose()
