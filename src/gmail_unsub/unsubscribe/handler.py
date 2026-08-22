"""Unsubscribe orchestrator with fallback chain."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from gmail_unsub.gmail.client import GmailClient
from gmail_unsub.gmail.models import (
    Subscription,
    UnsubscribeMethod,
    UnsubscribeResult,
    UnsubscribeStatus,
)
from gmail_unsub.storage.history import HistoryTracker
from gmail_unsub.unsubscribe.browser import BrowserHandler
from gmail_unsub.unsubscribe.mailto_handler import MailtoHandler
from gmail_unsub.unsubscribe.one_click import OneClickHandler


class UnsubscribeHandler:
    """
    Orchestrate unsubscribe attempts using fallback strategy.

    Priority:
    1. One-click HTTP POST (RFC 8058) - fastest and most reliable
    2. mailto: unsubscribe email
    3. Browser automation - for complex pages
    4. Mark as spam - last resort
    """

    def __init__(
        self,
        gmail_client: GmailClient,
        history: HistoryTracker,
        one_click_timeout: int = 30,
        browser_headless: bool = True,
        browser_timeout_ms: int = 30000,
        screenshots_dir: Path | None = None,
    ) -> None:
        self.gmail_client = gmail_client
        self.history = history

        self.one_click_handler = OneClickHandler(timeout=one_click_timeout)
        self.mailto_handler = MailtoHandler(gmail_client)
        self.browser_handler = BrowserHandler(
            headless=browser_headless,
            timeout_ms=browser_timeout_ms,
            screenshots_dir=screenshots_dir,
        )

    async def unsubscribe(
        self,
        subscription: Subscription,
        skip_browser: bool = False,
        skip_spam: bool = False,
    ) -> UnsubscribeResult:
        """
        Attempt to unsubscribe using the fallback chain.

        Args:
            subscription: The subscription to unsubscribe from
            skip_browser: Skip browser automation (useful for batch processing)
            skip_spam: Don't mark as spam if all methods fail
        """
        # Strategy 1: One-click HTTP POST
        if subscription.supports_one_click and subscription.list_unsubscribe_url:
            result = await self.one_click_handler.unsubscribe(subscription)
            if result.status == UnsubscribeStatus.SUCCESS:
                self.history.record(result)
                return result

        # Strategy 2: mailto: unsubscribe
        if subscription.list_unsubscribe_mailto:
            result = self.mailto_handler.unsubscribe(subscription)
            if result.status == UnsubscribeStatus.SUCCESS:
                self.history.record(result)
                return result

        # Strategy 3: Browser automation
        if not skip_browser and subscription.list_unsubscribe_url:
            result = await self.browser_handler.unsubscribe(subscription)
            if result.status == UnsubscribeStatus.SUCCESS:
                self.history.record(result)
                return result

        # Strategy 4: Mark as spam
        if not skip_spam:
            result = self._mark_as_spam(subscription)
            self.history.record(result)
            return result

        # All strategies failed/skipped
        result = UnsubscribeResult(
            sender_email=subscription.sender_email,
            sender_name=subscription.sender_name,
            method_used=UnsubscribeMethod.NOT_POSSIBLE,
            status=UnsubscribeStatus.FAILED,
            timestamp=datetime.now(),
            error_message="No unsubscribe method available",
        )
        self.history.record(result)
        return result

    def _mark_as_spam(self, subscription: Subscription) -> UnsubscribeResult:
        """Mark all messages from sender as spam."""
        try:
            self.gmail_client.mark_as_spam(subscription.message_ids)
            return UnsubscribeResult(
                sender_email=subscription.sender_email,
                sender_name=subscription.sender_name,
                method_used=UnsubscribeMethod.MARK_SPAM,
                status=UnsubscribeStatus.SUCCESS,
                timestamp=datetime.now(),
                details={
                    "messages_marked": len(subscription.message_ids),
                    "message_ids": subscription.message_ids,  # Store for undo
                },
            )
        except Exception as e:
            return UnsubscribeResult(
                sender_email=subscription.sender_email,
                sender_name=subscription.sender_name,
                method_used=UnsubscribeMethod.MARK_SPAM,
                status=UnsubscribeStatus.FAILED,
                timestamp=datetime.now(),
                error_message=f"Failed to mark as spam: {e}",
            )

    async def unsubscribe_batch(
        self,
        subscriptions: list[Subscription],
        skip_browser: bool = True,  # Skip browser for batch by default
        skip_spam: bool = False,
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> list[UnsubscribeResult]:
        """
        Process multiple unsubscribe requests.

        For batch processing, browser automation is skipped by default
        as it's slow and can be unreliable.
        """
        results = []
        total = len(subscriptions)

        for i, subscription in enumerate(subscriptions):
            if progress_callback:
                progress_callback(i + 1, total, subscription.sender_email)

            result = await self.unsubscribe(
                subscription,
                skip_browser=skip_browser,
                skip_spam=skip_spam,
            )
            results.append(result)

        return results

    def undo_spam(self, sender_email: str) -> bool:
        """Undo a spam marking by moving messages back to inbox."""
        # Find the spam result in history
        history_entries = self.history.get_by_sender(sender_email)

        for entry in history_entries:
            if entry.method_used == UnsubscribeMethod.MARK_SPAM:
                message_ids = entry.details.get("message_ids", [])
                if message_ids:
                    try:
                        self.gmail_client.remove_from_spam(message_ids)
                        return True
                    except Exception:
                        return False

        return False
