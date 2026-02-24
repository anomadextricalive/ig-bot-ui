"""
Instagram authentication using Playwright browser automation.
Uses a persistent browser context to maintain login across restarts.
"""

import logging
import os

from playwright.sync_api import sync_playwright, BrowserContext, Page

logger = logging.getLogger(__name__)

BROWSER_STATE_DIR = "browser_data"


def create_browser_context(playwright, headless=True):
    """
    Create a Playwright browser context with persistent storage.
    This keeps cookies/session across bot restarts.
    """
    os.makedirs(BROWSER_STATE_DIR, exist_ok=True)

    browser_context = playwright.chromium.launch_persistent_context(
        user_data_dir=BROWSER_STATE_DIR,
        headless=headless,
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-US",
    )

    return browser_context


def login_if_needed(context: BrowserContext, username: str, password: str) -> Page:
    """
    Check if already logged in. If not, perform login.
    Returns the main page.
    """
    page = context.new_page()

    # Go to Instagram login page directly
    logger.info("Navigating to Instagram...")
    page.goto("https://www.instagram.com/accounts/login/", timeout=30000)
    page.wait_for_timeout(5000)

    # Check if we're already logged in (redirected to home)
    current_url = page.url
    if "/accounts/login" not in current_url and "/challenge" not in current_url:
        if _is_logged_in(page):
            logger.info("Already logged in!")
            _dismiss_dialogs(page)
            return page

    # Handle cookie consent banner
    _dismiss_cookie_banner(page)

    # Wait for login form — if it's not there, we might be logged in
    try:
        page.wait_for_selector('input[name="email"]', timeout=10000)
    except Exception:
        # Maybe already logged in or on a different page
        if _is_logged_in(page):
            logger.info("Already logged in!")
            _dismiss_dialogs(page)
            return page
        else:
            # Try navigating to login page again
            page.goto("https://www.instagram.com/accounts/login/", timeout=30000)
            page.wait_for_timeout(5000)
            _dismiss_cookie_banner(page)
            page.wait_for_selector('input[name="email"]', timeout=15000)

    # Fill in credentials
    logger.info(f"Logging in as @{username}...")
    page.fill('input[name="email"]', username)
    page.wait_for_timeout(500)
    page.fill('input[name="pass"]', password)
    page.wait_for_timeout(500)

    # Submit the form by pressing Enter
    page.keyboard.press("Enter")

    # Wait for navigation
    page.wait_for_timeout(8000)

    # Dismiss post-login dialogs
    _dismiss_dialogs(page)

    if _is_logged_in(page):
        logger.info("Login successful!")
    else:
        # Check for challenge/verification page
        current_url = page.url
        if "challenge" in current_url:
            logger.warning("Instagram challenge detected. You may need to verify manually.")
            logger.warning(f"  Challenge URL: {current_url}")
        else:
            logger.warning("Login may have failed — proceeding anyway.")

    return page


def _dismiss_cookie_banner(page: Page):
    """Dismiss the cookie consent banner if present."""
    try:
        for text in ["Allow essential and optional cookies", "Allow all cookies", "Accept", "Accept All"]:
            btn = page.locator(f'button:has-text("{text}")')
            if btn.first.is_visible(timeout=2000):
                btn.first.click()
                page.wait_for_timeout(1000)
                return
    except Exception:
        pass


def _dismiss_dialogs(page: Page):
    """Dismiss the 'Save login info' and 'Turn on notifications' dialogs."""
    for _ in range(3):
        try:
            not_now = page.locator('button:has-text("Not Now"), button:has-text("Not now")')
            if not_now.first.is_visible(timeout=3000):
                not_now.first.click()
                page.wait_for_timeout(2000)
        except Exception:
            break


def _is_logged_in(page: Page) -> bool:
    """Check if the current page shows a logged-in state."""
    try:
        # Look for logged-in indicators (sidebar nav, Direct inbox link, etc.)
        for selector in [
            'a[href="/direct/inbox/"]',
            'svg[aria-label="Home"]',
            'svg[aria-label="Direct"]',
            'svg[aria-label="New post"]',
            'a[href="/explore/"]',
        ]:
            try:
                el = page.locator(selector)
                if el.first.is_visible(timeout=1500):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False
