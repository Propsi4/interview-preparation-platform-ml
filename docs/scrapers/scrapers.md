---
title: "Scrapers"
description: "Technical documentation for the Playwright-based web scraping subsystem."
---

# Scrapers

## Overview

The scraper subsystem uses **Playwright** (headless Chromium) to extract job vacancy listings from dou.ua, the largest Ukrainian IT job board. The system is designed with a pluggable architecture: a base `ScraperBase` class defines the interface, and concrete implementations handle site-specific behavior.

## Architecture

```mermaid
classDiagram
    direction TB

    class ScraperBase {
        <<abstract>>
        +source_name: str
        +headless: bool
        -_browser: Browser | None
        -_playwright: Playwright | None
        +get_browser() Browser
        +aclose() None
        +afetch(url) str | bytes
        +arun(*args) Iterable~dict~*
    }

    class DouScraper {
        +source_name: str = "dou.ua"
        -_base_url: str
        +arun(query) VacanciesOverviewSchema
        +scrape_vacancy(url) VacancySchema
        -_open_vacancies_page(query) Page
        -_extract_total_results(page) int | None
        -_expand_vacancies_list_page(page) Page
        -_extract_vacancies_urls_from_page(page) Iterable~str~
        -_safe_text(locator) str | None
    }

    ScraperBase <|-- DouScraper
```

## ScraperBase

**Location**: `src/scrapers/base.py`

The abstract base class provides:

| Method | Description |
|--------|-------------|
| `get_browser()` | Lazily initializes a Playwright Chromium browser instance |
| `aclose()` | Closes the browser and stops Playwright |
| `afetch(url)` | Opens a page, navigates to URL, and returns raw HTML |
| `arun(*args)` | **Abstract** — executes the full scraping pipeline |
| `run(*args)` | Sync wrapper via `asyncio.run()` |

The base class inherits from both `BaseModel` (Pydantic) and `ABC`, allowing scrapers to be configured via Pydantic fields while enforcing the scraper interface.

## DouScraper

**Location**: `src/scrapers/implementations/dou.py`

### Two-Phase Scraping

The dou.ua scraper operates in two distinct phases:

#### Phase 1: Overview Scrape

Collects all vacancy **URLs** for a search query.

```mermaid
graph TD
    subgraph Phase1["Phase 1: Overview"]
        style Phase1 fill:#161b22,stroke:#30363d,color:#e6edf3
        A["Open search page<br>jobs.dou.ua/vacancies/?search=QUERY"]
        B["Extract total results count<br>from .b-inner-page-header"]
        C["Click 'Load more' button<br>until no more results"]
        D["Extract all vacancy URLs<br>from a.vt elements"]
        E["Return VacanciesOverviewSchema"]
    end

    A --> B --> C --> D --> E
```

**Key implementation details**:

- **Load More expansion** (`_expand_vacancies_list_page`): Uses jQuery-style trigger simulation (`mousedown` → `mouseup` → `click`) because dou.ua uses Ajax pagination
- **Total results extraction** (`_extract_total_results`): Parses the page header with regex to find the vacancy count
- **Safe text extraction** (`_safe_text`): Catches all exceptions and normalizes whitespace with `re.sub(r'\s+', ' ', text)`

#### Phase 2: Detail Scrape

Extracts full details from each individual vacancy page.

```mermaid
graph TD
    subgraph Phase2["Phase 2: Details"]
        style Phase2 fill:#161b22,stroke:#30363d,color:#e6edf3
        A["Navigate to vacancy URL"]
        B["Extract in parallel:<br>title, company, location, description"]
        C["Return VacancySchema"]
    end

    A --> B --> C
```

**Performance optimization**: The `scrape_vacancy()` method uses `asyncio.gather()` to extract title, company, location, and description in parallel.

## Data Schemas

**Location**: `src/scrapers/schemas/vacancy.py`

### VacancySchema

Represents a single scraped vacancy:

```python
class VacancySchema(BaseModel):
    title: str         # Vacancy title
    company: str       # Company name
    location: str | None  # Location (may be remote)
    description: str   # Full vacancy description
    url: str           # Source URL

    model_config = ConfigDict(from_attributes=True)  # ORM compatibility
```

### VacanciesOverviewSchema

Represents the overview scrape result:

```python
class VacanciesOverviewSchema(BaseModel):
    query: str              # Original search query
    total_results: int      # Total vacancies found
    vacancies_urls: List[str]  # Extracted URLs
```

## Integration with Celery

The scrapers are invoked exclusively through Celery tasks:

| Task | Queue | Rate Limit | Retries |
|------|-------|------------|---------|
| `scrape_vacancies_overview` | `scrapers` | `40/m` | 3 |
| `scrape_vacancy_details` | `scrapers` | `20/m` | 3 |

**Task chaining**: Overview → per-vacancy detail scrapes → (when all done) → requirements unification.

See [Celery Tasks](../jobs/celery_tasks.md) for the full task pipeline documentation.

## Adding a New Scraper

To add support for a new job board:

1. Create a new file in `src/scrapers/implementations/`
2. Extend `ScraperBase` and implement `arun()`
3. Add corresponding Celery tasks in `src/jobs/tasks/`
4. Register the tasks in `src/jobs/tasks/__init__.py`

```python
from src.scrapers.base import ScraperBase

class NewBoardScraper(ScraperBase):
    source_name: str = "newboard.com"

    async def arun(self, query: str) -> VacanciesOverviewSchema:
        # Implement scraping logic here
        ...
```
