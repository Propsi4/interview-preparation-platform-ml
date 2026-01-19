"""Async scraper for dou.ua vacancies.

Examples
--------
>>> import asyncio
>>> from ml.scrapers.dou import DouScraper
>>> asyncio.run(DouScraper().async_run("HR"))
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from playwright.async_api import Browser, Locator, Page, async_playwright
from pydantic import PrivateAttr

from ml.db.engine import get_sessionmaker
from ml.db.models.search_query import SearchQuery
from ml.db.models.vacancies import Vacancy
from ml.scrapers.base import ScraperBase

from ml.core.logging import logger


class DouScraper(ScraperBase):
    """Scraper for dou.ua vacancies using Playwright."""

    source_name: str = "dou.ua"
    _base_url: str = PrivateAttr(default="https://jobs.dou.ua/vacancies/")

    async def _open_vacancies_page(self, query: str) -> Page:
        """Open the vacancies page for a query."""
        page = await self.browser.new_page()
        await page.goto(f"{self._base_url}?search=={query}")
        return page

    async def _extract_total_results(self, page: Page) -> int | None:
        """Extract total results count from the page."""
        total_results = await page.locator(".b-inner-page-header").text_content()
        # extract all the continuous numbers from the beginning of the string
        match = re.search(r"\d+", total_results)
        if match:
            return int(match.group(0))
        return None

    async def run(self, query: str) -> Iterable[dict[str, Any]]:
        """Scrape vacancies for a query.

        Parameters
        ----------
        query : str
            Search query to submit on dou.ua (e.g., "HR").
        """
        page = await self._open_vacancies_page(query)
        total_results = await self._extract_total_results(page)
        return total_results
    # async def async_run(self, query: str) -> Sequence[Vacancy]:
    #     """Scrape vacancies for a query and persist results.

    #     Parameters
    #     ----------
    #     query : str
    #         Search query to submit on dou.ua (e.g., "HR").

    #     Returns
    #     -------
    #     Sequence[Vacancy]
    #         Persisted vacancy rows for the query.
    #     """

    #     sessionmaker = get_sessionmaker()
    #     results: list[Vacancy] = []

    #     async with sessionmaker() as session:
    #         search_query = SearchQuery(query=query, total_results=None, processed_results=0)
    #         session.add(search_query)
    #         await session.commit()
    #         await session.refresh(search_query)

    #         async with async_playwright() as playwright:
    #             browser = await playwright.chromium.launch(headless=True)
    #             try:
    #                 page = await browser.new_page()
    #                 await page.goto(VACANCIES_URL)
    #                 await _submit_query(page, query)

    #                 total_results = await _extract_total_results(page)
    #                 vacancy_cards = page.locator("div.vacancy")
    #                 cards_count = await vacancy_cards.count()
    #                 if total_results is None:
    #                     total_results = cards_count

    #                 search_query.total_results = total_results
    #                 await session.commit()

    #                 for index in range(cards_count):
    #                     card = vacancy_cards.nth(index)
    #                     try:
    #                         card_data = await _extract_card_data(card)
    #                         detail_data = await _extract_detail_data(browser, card_data["url"])
    #                         vacancy = Vacancy(
    #                             search_query_id=search_query.id,
    #                             title=card_data["title"],
    #                             company=card_data["company"],
    #                             location=detail_data["location"],
    #                             description=detail_data["description"],
    #                             url=card_data["url"],
    #                         )
    #                         session.add(vacancy)
    #                         search_query.processed_results = index + 1
    #                         await session.commit()
    #                         results.append(vacancy)
    #                     except Exception:
    #                         await session.rollback()
    #                         logger.exception("Failed to scrape vacancy at index %s", index)
    #                         continue
    #             finally:
    #                 await browser.close()

    #     return results


async def _submit_query(page: Page, query: str) -> None:
    """Submit the search query on the vacancies page.

    Parameters
    ----------
    page : Page
        Playwright page instance.
    query : str
        Query to submit.

    Returns
    -------
    None
        No return value.
    """

    await page.wait_for_selector("input[name='search'], input#search, input#query")
    search_input = page.locator("input[name='search'], input#search, input#query").first
    await search_input.fill(query)
    await search_input.press("Enter")
    await page.wait_for_load_state("networkidle")


async def _extract_total_results(page: Page) -> int | None:
    """Extract total results count from the page.

    Parameters
    ----------
    page : Page
        Playwright page instance.

    Returns
    -------
    int | None
        Parsed total results or None if not found.
    """

    selectors = [
        ".b-vacancies-head__title",
        ".b-vacancies-head",
        ".b-result",
        ".vacancies-control",
    ]
    for selector in selectors:
        text = await _safe_text(page.locator(selector).first)
        count = _parse_first_int(text)
        if count is not None:
            return count
    return None


async def _extract_card_data(card: Locator) -> dict[str, str]:
    """Extract listing data from a vacancy card.

    Parameters
    ----------
    card : Page
        Playwright locator for a vacancy card.

    Returns
    -------
    dict[str, str]
        Extracted title, company, and url values.
    """

    title_locator = card.locator("a.vt, a.title").first
    title = await _safe_text(title_locator)
    url = await title_locator.get_attribute("href")
    company = await _safe_text(card.locator(".company a, .company, .l-n a").first)

    if not url:
        raise ValueError("Vacancy URL not found.")

    return {
        "title": title or "Untitled vacancy",
        "company": company or "Unknown company",
        "url": _ensure_absolute_url(url),
    }


async def _extract_detail_data(browser: Browser, url: str) -> dict[str, str | None]:
    """Extract details from a vacancy page.

    Parameters
    ----------
    browser : Browser
        Playwright browser instance.
    url : str
        Vacancy URL.

    Returns
    -------
    dict[str, str | None]
        Extracted description and location values.
    """

    page = await browser.new_page()
    try:
        await page.goto(url)
        await page.wait_for_load_state("networkidle")
        description = await _safe_text(
            page.locator("div.b-typo, .b-vacancy-section, .vacancy-section, .l-vacancy").first
        )
        location = await _safe_text(page.locator(".place, .location, .city").first)
        return {
            "description": description or "",
            "location": location,
        }
    finally:
        await page.close()


async def _safe_text(locator: Locator) -> str | None:
    """Safely read text content from a locator.

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
    except Exception:
        return None
    if text is None:
        return None
    return text.strip()


def _parse_first_int(text: str | None) -> int | None:
    """Parse the first integer from a text blob.

    Parameters
    ----------
    text : str | None
        Text to parse.

    Returns
    -------
    int | None
        Parsed integer if found.
    """

    if not text:
        return None
    match = re.search(r"\d[\d\s]*", text)
    if not match:
        return None
    return int(match.group(0).replace(" ", ""))


def _ensure_absolute_url(url: str) -> str:
    """Normalize vacancy URLs to absolute form.

    Parameters
    ----------
    url : str
        Vacancy URL.

    Returns
    -------
    str
        Absolute URL.
    """

    if url.startswith("http"):
        return url
    return f"{BASE_URL}{url}"
