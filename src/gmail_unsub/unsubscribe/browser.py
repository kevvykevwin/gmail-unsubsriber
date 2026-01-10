"""Browser automation for complex unsubscribe pages using Playwright."""

import re
from datetime import datetime
from pathlib import Path

from gmail_unsub.gmail.models import Subscription, UnsubscribeMethod, UnsubscribeResult, UnsubscribeStatus
from gmail_unsub.utils.url_validator import is_safe_url


class BrowserHandler:
    """Handle unsubscribe pages that require browser interaction."""

    # Button/link selectors to try, in priority order
    UNSUBSCRIBE_SELECTORS = [
        'button:has-text("unsubscribe")',
        'a:has-text("unsubscribe")',
        'input[type="submit"][value*="unsubscribe" i]',
        'button:has-text("confirm")',
        'a:has-text("confirm")',
        'button:has-text("yes")',
        'button:has-text("remove")',
        'a:has-text("remove")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]

    # Patterns indicating successful unsubscribe
    SUCCESS_PATTERNS = [
        "successfully unsubscribed",
        "you have been unsubscribed",
        "unsubscribe confirmed",
        "removed from",
        "no longer receive",
        "opt-out successful",
        "unsubscription complete",
        "you've been removed",
        "email preferences updated",
    ]

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        screenshots_dir: Path | None = None,
    ) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.screenshots_dir = screenshots_dir

    async def unsubscribe(self, subscription: Subscription) -> UnsubscribeResult:
        """
        Use Playwright to automate unsubscribe page interaction.
        """
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

        url = subscription.list_unsubscribe_url
        if not url:
            return self._fail_result(subscription, "No unsubscribe URL available")

        # Validate URL is safe (HTTPS, not internal/private)
        is_safe, error = is_safe_url(url)
        if not is_safe:
            return self._fail_result(subscription, f"Unsafe URL: {error}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                # Navigate to the unsubscribe page
                await page.goto(url, wait_until="networkidle", timeout=self.timeout_ms)

                # Check if already shows success
                if await self._check_success_indicators(page):
                    return UnsubscribeResult(
                        sender_email=subscription.sender_email,
                        sender_name=subscription.sender_name,
                        method_used=UnsubscribeMethod.BROWSER,
                        status=UnsubscribeStatus.SUCCESS,
                        timestamp=datetime.now(),
                        details={"url": url, "immediate_success": True},
                    )

                # Try to find and click unsubscribe button
                success = await self._try_auto_unsubscribe(page)

                if success:
                    return UnsubscribeResult(
                        sender_email=subscription.sender_email,
                        sender_name=subscription.sender_name,
                        method_used=UnsubscribeMethod.BROWSER,
                        status=UnsubscribeStatus.SUCCESS,
                        timestamp=datetime.now(),
                        details={"url": url},
                    )

                # Could not auto-complete - save screenshot for debugging
                screenshot_path = None
                if self.screenshots_dir:
                    self.screenshots_dir.mkdir(parents=True, exist_ok=True)
                    # Sanitize filename to prevent path traversal
                    safe_email = re.sub(r"[^\w\-@.]", "_", subscription.sender_email)
                    safe_email = safe_email.replace("@", "_at_").replace(".", "_")
                    screenshot_path = self.screenshots_dir / f"{safe_email}.png"
                    await page.screenshot(path=screenshot_path)

                return self._fail_result(
                    subscription,
                    "Could not automate unsubscribe - page may require manual interaction",
                    {"url": url, "screenshot": str(screenshot_path) if screenshot_path else None},
                )

            except PlaywrightTimeout:
                return self._fail_result(subscription, "Page load timeout", {"url": url})
            except Exception as e:
                return self._fail_result(subscription, f"Browser error: {e}", {"url": url})
            finally:
                await browser.close()

    async def _try_auto_unsubscribe(self, page) -> bool:
        """
        Attempt to find and click unsubscribe buttons/links.

        Returns True if unsubscribe appears successful.
        """
        from playwright.async_api import TimeoutError as PlaywrightTimeout

        for selector in self.UNSUBSCRIBE_SELECTORS:
            try:
                locator = page.locator(selector).first
                if not await locator.is_visible(timeout=2000):
                    continue

                await locator.click()
                await page.wait_for_load_state("networkidle", timeout=10000)

                if await self._check_success_indicators(page):
                    return True

                # Check if another button appeared (multi-step unsubscribe)
                if await self._try_confirmation_step(page):
                    return True

            except (PlaywrightTimeout, Exception):
                continue

        return False

    async def _try_confirmation_step(self, page) -> bool:
        """Try to click a confirmation button in multi-step unsubscribe flows."""
        from playwright.async_api import TimeoutError as PlaywrightTimeout

        for confirm_selector in self.UNSUBSCRIBE_SELECTORS[:6]:
            try:
                confirm_locator = page.locator(confirm_selector).first
                if await confirm_locator.is_visible(timeout=1000):
                    await confirm_locator.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    if await self._check_success_indicators(page):
                        return True
            except (PlaywrightTimeout, Exception):
                continue
        return False

    async def _check_success_indicators(self, page) -> bool:
        """Check if page shows unsubscribe success."""
        try:
            content = await page.content()
            content_lower = content.lower()
            return any(pattern in content_lower for pattern in self.SUCCESS_PATTERNS)
        except Exception:
            return False

    def _fail_result(
        self,
        subscription: Subscription,
        error_message: str,
        details: dict | None = None,
    ) -> UnsubscribeResult:
        """Create a failed unsubscribe result."""
        return UnsubscribeResult(
            sender_email=subscription.sender_email,
            sender_name=subscription.sender_name,
            method_used=UnsubscribeMethod.BROWSER,
            status=UnsubscribeStatus.FAILED,
            timestamp=datetime.now(),
            error_message=error_message,
            details=details or {},
        )
