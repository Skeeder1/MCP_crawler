"""
Base scraper class using Playwright for web scraping
Provides common scraping functionality with anti-detection measures
"""
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
import asyncio
from typing import Optional, List
import random


class BaseScraper:
    """
    Base scraper using Playwright for robust web scraping
    Supports headless mode, custom user agents, and anti-detection measures
    """

    def __init__(self, headless: bool = True, user_agent: Optional[str] = None, viewport: Optional[dict] = None):
        """
        Initialize the scraper

        Args:
            headless: Run browser in headless mode
            user_agent: Custom user agent string
            viewport: Custom viewport size {'width': 1920, 'height': 1080}
        """
        self.headless = headless
        self.user_agent = user_agent
        self.viewport = viewport or {'width': 1920, 'height': 1080}

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self):
        """Start the browser and create a new page"""
        self.playwright = await async_playwright().start()

        # Launch browser with anti-detection settings
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )

        logger.info("Browser started")

        # Create context with custom settings
        context_options = {
            'viewport': self.viewport,
            'user_agent': self.user_agent or await self._get_default_user_agent(),
        }

        self.context = await self.browser.new_context(**context_options)

        # Add init script to hide webdriver property
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = await self.context.new_page()
        logger.info("Page created")

    async def _get_default_user_agent(self):
        """Get a realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        return random.choice(user_agents)

    async def navigate(self, url: str, timeout: int = 60000, wait_until: str = 'domcontentloaded'):
        """
        Navigate to a URL

        Args:
            url: URL to navigate to
            timeout: Navigation timeout in milliseconds
            wait_until: When to consider navigation succeeded ('load', 'domcontentloaded', 'networkidle')

        Returns:
            bool: True if navigation succeeded, False otherwise
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")

        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, timeout=timeout, wait_until=wait_until)
            logger.info(f"Navigation complete: {url}")
            return True
        except Exception as e:
            logger.warning(f"Navigation failed for {url}: {e}")
            return False

    async def get_html(self) -> str:
        """Get the current page HTML content"""
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")
        return await self.page.content()

    async def get_text(self, selector: str) -> Optional[str]:
        """
        Get text content of an element

        Args:
            selector: CSS selector

        Returns:
            Text content or None if element not found
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")

        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return None
        except Exception as e:
            logger.warning(f"Error getting text for selector '{selector}': {e}")
            return None

    async def get_all_hrefs(self, selector: str = 'a') -> List[str]:
        """
        Get all href attributes matching a selector

        Args:
            selector: CSS selector for links

        Returns:
            List of href URLs
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")

        try:
            elements = await self.page.query_selector_all(selector)
            hrefs = []
            for element in elements:
                href = await element.get_attribute('href')
                if href:
                    hrefs.append(href)
            return hrefs
        except Exception as e:
            logger.warning(f"Error getting hrefs for selector '{selector}': {e}")
            return []

    async def click(self, selector: str, timeout: int = 30000):
        """
        Click on an element

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")

        try:
            await self.page.click(selector, timeout=timeout)
            logger.debug(f"Clicked: {selector}")
        except Exception as e:
            logger.warning(f"Error clicking selector '{selector}': {e}")
            raise

    async def wait_for_selector(self, selector: str, timeout: int = 30000, state: str = 'visible'):
        """
        Wait for a selector to appear

        Args:
            selector: CSS selector
            timeout: Timeout in milliseconds
            state: Element state to wait for ('attached', 'detached', 'visible', 'hidden')
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")

        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            logger.debug(f"Selector appeared: {selector}")
        except Exception as e:
            logger.warning(f"Timeout waiting for selector '{selector}': {e}")
            raise

    async def query_selector(self, selector: str):
        """
        Query a single element

        Args:
            selector: CSS selector

        Returns:
            ElementHandle or None
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")
        return await self.page.query_selector(selector)

    async def query_selector_all(self, selector: str):
        """
        Query all elements matching selector

        Args:
            selector: CSS selector

        Returns:
            List of ElementHandles
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")
        return await self.page.query_selector_all(selector)

    async def evaluate(self, script: str):
        """
        Execute JavaScript in page context

        Args:
            script: JavaScript code to execute

        Returns:
            Result of script execution
        """
        if not self.page:
            raise RuntimeError("Scraper not started. Call start() first.")
        return await self.page.evaluate(script)

    async def close(self):
        """Close the browser and cleanup resources"""
        if self.page:
            await self.page.close()
            logger.info("Page closed")

        if self.context:
            await self.context.close()
            logger.info("Context closed")

        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright stopped")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
