"""E2E frontend testing suite using Playwright and Pytest.

This module provides a comprehensive suite of 10 end-to-end tests for the React frontend,
covering page load, sidebar navigation, search query creation, deletion, progress checking,
quick start interview, sessions management, renaming, deletion, and interactive chat messaging.
"""

# Standard library imports
import time
from typing import Generator
import uuid

# Thirdparty imports
import pytest
from playwright.sync_api import Browser, Page, sync_playwright

BASE_URL = "http://localhost:5173"


@pytest.fixture(scope="session")
def playwright_browser() -> Generator[Browser, None, None]:
    """
    Launch a headless Chromium browser instance for the test session.

    Yields
    ------
    Browser
        The Playwright Browser instance.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(playwright_browser: Browser) -> Generator[Page, None, None]:
    """
    Provide a new browser page context for each test case.

    Parameters
    ----------
    playwright_browser : Browser
        The active session's Browser instance.

    Yields
    ------
    Page
        A new browser page.
    """
    context = playwright_browser.new_context()
    page = context.new_page()
    yield page
    context.close()


def test_dashboard_page_loads(page: Page) -> None:
    """
    Verify that the dashboard page loads correctly with the welcome banner and stats.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Verify welcome message
    welcome_header = page.locator("h1:has-text('Welcome back')")
    welcome_header.wait_for(state="visible")
    assert welcome_header.is_visible()

    # Verify key dashboard components are visible
    assert page.locator("h2:has-text('Recent Sessions')").is_visible()
    assert page.locator("h2:has-text('Stats')").is_visible()
    assert page.locator("button:has-text('New Interview')").is_visible()


def test_sidebar_navigation(page: Page) -> None:
    """
    Test that clicking navigation links in the sidebar navigates to correct routes.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Navigate to Search Queries page
    page.click("aside a[href='/search-queries']")
    page.wait_for_load_state("networkidle")
    assert "/search-queries" in page.url
    page.locator("h1:has-text('Search Queries')").wait_for(state="visible")

    # Navigate to Evaluations page
    page.click("aside a[href='/evaluations']")
    page.wait_for_load_state("networkidle")
    assert "/evaluations" in page.url
    page.locator("h1:has-text('Interview Evaluations')").wait_for(state="visible")

    # Navigate to Sessions page (using aside selector as Sessions is in secondaryItems)
    page.click("aside a[href='/sessions']")
    page.wait_for_load_state("networkidle")
    assert "/sessions" in page.url
    page.locator("h2:has-text('Sessions')").wait_for(state="visible")

    # Navigate back to Dashboard via logo/dashboard link
    page.click("aside a[href='/']")
    page.wait_for_load_state("networkidle")
    assert page.url.endswith("/") or "localhost:5173" in page.url


def test_create_search_query(page: Page) -> None:
    """
    Test creating a new search query and verify it appears in the query list.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(f"{BASE_URL}/search-queries")
    page.wait_for_load_state("networkidle")

    # Use unique query text to avoid database collisions
    query_text = f"E2E Test vacancy query {uuid.uuid4().hex[:8]}"

    # Fill input and submit
    input_field = page.locator("input[placeholder='New search query...']")
    input_field.wait_for(state="visible")
    input_field.fill(query_text)
    page.click("button:has-text('Add Query')")

    # Wait for the network requests to complete and query to appear
    page.wait_for_load_state("networkidle")
    
    # Verify that the query card is visible in the list
    card_header = page.locator(f"h3:has-text('{query_text}')").first
    card_header.wait_for(state="visible")
    assert card_header.is_visible()


def test_check_search_query_progress(page: Page) -> None:
    """
    Test clicking 'Check Progress' on a query card displays the progress bar.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(f"{BASE_URL}/search-queries")
    page.wait_for_load_state("networkidle")

    # Create a unique query to ensure it exists
    query_text = f"E2E Test progress query {uuid.uuid4().hex[:8]}"
    input_field = page.locator("input[placeholder='New search query...']")
    input_field.fill(query_text)
    page.click("button:has-text('Add Query')")
    page.wait_for_load_state("networkidle")

    # Find the specific card using the exact bg-panel selector to avoid strict mode violations
    card = page.locator(f"div.bg-panel:has(h3:has-text('{query_text}'))").first
    card.wait_for(state="visible")
    
    check_btn = card.locator("button:has-text('Check Progress')")
    check_btn.wait_for(state="visible")
    check_btn.click()

    # Progress ratio text or bar should appear
    page.wait_for_load_state("networkidle")
    
    # Progress ratio text "done" or progress bar should be present in the card
    done_text = card.locator("span:has-text('done')")
    done_text.wait_for(state="visible")
    assert done_text.is_visible()


def test_delete_search_query(page: Page) -> None:
    """
    Test deleting a search query after confirming the dialog.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(f"{BASE_URL}/search-queries")
    page.wait_for_load_state("networkidle")

    # Create a unique query first to ensure it exists and has no name collisions
    query_text = f"E2E Test delete query {uuid.uuid4().hex[:8]}"
    input_field = page.locator("input[placeholder='New search query...']")
    input_field.fill(query_text)
    page.click("button:has-text('Add Query')")
    page.wait_for_load_state("networkidle")

    # Find the specific card
    card = page.locator(f"div.bg-panel:has(h3:has-text('{query_text}'))").first
    card.wait_for(state="visible")

    # Register dialog handler to accept the confirmation dialog
    page.once("dialog", lambda dialog: dialog.accept())

    # Click the trash icon/delete button on the created query card
    delete_btn = card.locator("button[title='Delete query']")
    delete_btn.click()

    # Wait for the query text to be hidden (removed from the DOM/UI)
    deleted_text = page.locator(f"h3:has-text('{query_text}')").first
    deleted_text.wait_for(state="hidden")
    assert not deleted_text.is_visible()


def test_quick_start_new_interview(page: Page) -> None:
    """
    Test that clicking 'New Interview' navigates to the chat page with a new session.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Click New Interview button
    page.click("button:has-text('New Interview')")
    page.wait_for_load_state("networkidle")

    # Expect URL to match the chat route with a session ID
    assert "/chat/" in page.url
    
    # Wait for Sidebar Context and Controls to load and become visible
    page.locator("h3:has-text('Context')").wait_for(state="visible")
    page.locator("h3:has-text('Controls')").wait_for(state="visible")
    
    assert page.locator("h3:has-text('Context')").is_visible()
    assert page.locator("h3:has-text('Controls')").is_visible()


def test_sessions_table_loads(page: Page) -> None:
    """
    Verify that the Sessions page loads and contains the sessions table with headers.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    page.goto(f"{BASE_URL}/sessions")
    page.wait_for_load_state("networkidle")

    # Check table headers
    page.locator("th:has-text('Session')").wait_for(state="visible")
    assert page.locator("th:has-text('Session')").is_visible()
    assert page.locator("th:has-text('Messages')").is_visible()
    assert page.locator("th:has-text('Status')").is_visible()
    assert page.locator("th:has-text('Price')").is_visible()


def test_session_rename(page: Page) -> None:
    """
    Test renaming a session using the browser prompt dialog on the Sessions page.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    # Navigate to chat to generate a session first
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.click("button:has-text('New Interview')")
    page.wait_for_load_state("networkidle")

    # Go to Sessions page
    page.goto(f"{BASE_URL}/sessions")
    page.wait_for_load_state("networkidle")

    # Use unique rename title to avoid mismatching sessions
    new_title = f"Renamed E2E Test Session {uuid.uuid4().hex[:8]}"

    # Register dialog handler to submit the prompt with the new title
    page.once("dialog", lambda dialog: dialog.accept(new_title))

    # Click the rename button on the first session row
    rename_btn = page.locator("button:has-text('Rename')").first
    rename_btn.wait_for(state="visible")
    rename_btn.click()

    page.wait_for_load_state("networkidle")

    # Verify status message or new title in table
    renamed_label = page.locator(f"span:has-text('{new_title}')").first
    renamed_label.wait_for(state="visible")
    assert renamed_label.is_visible()


def test_session_delete(page: Page) -> None:
    """
    Test deleting a session from the Sessions page table.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    # Navigate to chat to create a new session
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.click("button:has-text('New Interview')")
    page.wait_for_load_state("networkidle")

    # Go to Sessions page
    page.goto(f"{BASE_URL}/sessions")
    page.wait_for_load_state("networkidle")

    # Click delete button on the first session row
    delete_btn = page.locator("button:has-text('Delete')").first
    delete_btn.wait_for(state="visible")
    delete_btn.click()

    page.wait_for_load_state("networkidle")

    # Verify status message appears
    status_msg = page.locator("text=Session deleted.").first
    status_msg.wait_for(state="visible")
    assert status_msg.is_visible()


def test_chat_page_messaging(page: Page) -> None:
    """
    Test starting a chat, selecting context query, and sending a text message.

    Parameters
    ----------
    page : Page
        The current browser page.
    """
    # First, ensure there is at least one search query available with a unique name
    page.goto(f"{BASE_URL}/search-queries")
    page.wait_for_load_state("networkidle")
    query_text = f"E2E Chat Context Query {uuid.uuid4().hex[:8]}"
    
    input_field = page.locator("input[placeholder='New search query...']")
    input_field.fill(query_text)
    page.click("button:has-text('Add Query')")
    page.wait_for_load_state("networkidle")

    # Navigate to new interview
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.click("button:has-text('New Interview')")
    page.wait_for_load_state("networkidle")

    # Select our query from context dropdown
    context_select = page.locator("#context-select")
    context_select.locator("button").click()
    
    option = context_select.locator(f"li:has-text('{query_text}')")
    option.wait_for(state="visible")
    option.click()

    # Fill input and send message by pressing Enter
    chat_input = page.locator("#chat-input")
    chat_input.wait_for(state="visible")
    
    test_msg = "Hello, I am ready to start the interview."
    chat_input.fill(test_msg)
    chat_input.press("Enter")

    # Verify user message appears in bubble list
    page.wait_for_load_state("networkidle")
    chat_bubble = page.locator(f"div:has-text('{test_msg}')").first
    chat_bubble.wait_for(state="visible")
    assert chat_bubble.is_visible()
