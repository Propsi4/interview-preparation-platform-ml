"""Base scraper class for all scrapers."""

from abc import ABC, abstractmethod
from typing import Any, Iterable
from playwright.async_api import Browser, Playwright, async_playwright

from pydantic import BaseModel, Field, PrivateAttr
import asyncio


class ScraperBase(BaseModel, ABC):
    """Base contract for all scrapers.

    Defines the minimal interface a scraper must implement and provides a
    template method that orchestrates the scrape flow. Concrete scrapers
    should focus on site-specific behavior only.
    """

    source_name: str = Field(description="Name of the source to scrape")
    headless: bool = Field(default=True)
    _browser: Browser | None = PrivateAttr(default=None)
    _playwright: Playwright | None = PrivateAttr(default=None)

    async def get_browser(self) -> Browser:
        """Get the browser instance."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
        return self._browser

    async def aclose(self) -> None:
        """Close the browser instance."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    def close(self) -> None:
        """Close the browser instance."""
        asyncio.run(self.aclose())

    async def afetch(self, url: str, *args: Any, **kwargs: Any) -> str | bytes:
        """Retrieve raw data from the source.

        Returns
        -------
        str | bytes
            Raw response payload from the target source.
        """
        browser = await self.get_browser()
        page = await browser.new_page()
        await page.goto(url)
        return await page.content()

    def fetch(self, url: str, *args: Any, **kwargs: Any) -> str | bytes:
        """Retrieve raw data from the source."""
        return asyncio.run(self.afetch(url, *args, **kwargs))

    @abstractmethod
    async def arun(self, *args: Any, **kwargs: Any) -> Iterable[dict[str, Any]]:
        """
        Execute the full scraping pipeline.

        Returns
        -------
        Iterable[dict[str, Any]]
            Normalized records produced by the scraper.
        """

    def run(self, *args: Any, **kwargs: Any) -> Iterable[dict[str, Any]]:
        """
        Execute the scraper asynchronously.

        Parameters
        ----------
        query : str
            Search query to execute for the scraper.

        Returns
        -------
        Iterable[dict[str, Any]]
            Normalized records produced by the scraper.
        """
        return asyncio.run(self.arun(*args, **kwargs))
