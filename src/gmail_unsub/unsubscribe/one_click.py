"""RFC 8058 one-click unsubscribe handler."""

from datetime import datetime

import httpx

from gmail_unsub.gmail.models import Subscription, UnsubscribeMethod, UnsubscribeResult, UnsubscribeStatus
from gmail_unsub.utils.url_validator import is_safe_url


class OneClickHandler:
    """Handle RFC 8058 one-click unsubscribe requests."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    async def unsubscribe(self, subscription: Subscription) -> UnsubscribeResult:
        """
        Perform RFC 8058 one-click unsubscribe.

        Requirements per RFC 8058:
        - POST request to HTTPS URI from List-Unsubscribe header
        - Body: List-Unsubscribe=One-Click
        - Content-Type: application/x-www-form-urlencoded
        """
        if not subscription.supports_one_click:
            return self._fail_result(subscription, "One-click not supported for this sender")

        url = subscription.list_unsubscribe_url
        if not url:
            return self._fail_result(subscription, "No unsubscribe URL available")

        # Validate URL is safe (HTTPS, not internal/private)
        is_safe, error = is_safe_url(url)
        if not is_safe:
            return self._fail_result(subscription, f"Unsafe URL: {error}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data="List-Unsubscribe=One-Click",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    timeout=self.timeout,
                    follow_redirects=True,
                )

                # Success: 2xx status codes
                if 200 <= response.status_code < 300:
                    return UnsubscribeResult(
                        sender_email=subscription.sender_email,
                        sender_name=subscription.sender_name,
                        method_used=UnsubscribeMethod.ONE_CLICK_HTTP,
                        status=UnsubscribeStatus.SUCCESS,
                        timestamp=datetime.now(),
                        details={"status_code": response.status_code, "url": url},
                    )
                else:
                    return self._fail_result(
                        subscription,
                        f"HTTP {response.status_code}",
                        {"status_code": response.status_code, "url": url},
                    )

        except httpx.TimeoutException:
            return self._fail_result(subscription, "Request timed out", {"url": url})
        except httpx.RequestError as e:
            return self._fail_result(subscription, f"Request failed: {e}", {"url": url})
        except Exception as e:
            return self._fail_result(subscription, f"Unexpected error: {e}", {"url": url})

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
            method_used=UnsubscribeMethod.ONE_CLICK_HTTP,
            status=UnsubscribeStatus.FAILED,
            timestamp=datetime.now(),
            error_message=error_message,
            details=details or {},
        )
