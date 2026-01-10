"""Mailto unsubscribe handler - sends email via Gmail API."""

from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

from gmail_unsub.gmail.client import GmailClient
from gmail_unsub.gmail.models import Subscription, UnsubscribeMethod, UnsubscribeResult, UnsubscribeStatus


class MailtoHandler:
    """Handle mailto: unsubscribe requests by sending email via Gmail API."""

    def __init__(self, gmail_client: GmailClient) -> None:
        self.gmail_client = gmail_client

    def unsubscribe(self, subscription: Subscription) -> UnsubscribeResult:
        """
        Send unsubscribe email using mailto: URL.

        Parses the mailto: URL for:
        - Recipient email
        - Subject (if provided)
        - Body (if provided)
        """
        mailto_url = subscription.list_unsubscribe_mailto
        if not mailto_url:
            return self._fail_result(subscription, "No mailto URL available")

        # Parse mailto URL
        try:
            to, subject, body = self._parse_mailto(mailto_url)
        except Exception as e:
            return self._fail_result(subscription, f"Failed to parse mailto URL: {e}")

        if not to:
            return self._fail_result(subscription, "No recipient in mailto URL")

        # Send the email
        try:
            result = self.gmail_client.send_message(
                to=to,
                subject=subject or "Unsubscribe",
                body=body or "Please unsubscribe me from this mailing list.",
            )

            return UnsubscribeResult(
                sender_email=subscription.sender_email,
                sender_name=subscription.sender_name,
                method_used=UnsubscribeMethod.MAILTO,
                status=UnsubscribeStatus.SUCCESS,
                timestamp=datetime.now(),
                details={
                    "mailto": mailto_url,
                    "sent_to": to,
                    "message_id": result.get("id"),
                },
            )

        except Exception as e:
            return self._fail_result(
                subscription,
                f"Failed to send email: {e}",
                {"mailto": mailto_url, "sent_to": to},
            )

    def _parse_mailto(self, mailto_url: str) -> tuple[str, str | None, str | None]:
        """
        Parse a mailto: URL.

        Returns:
            Tuple of (recipient, subject, body)
        """
        if not mailto_url.startswith("mailto:"):
            raise ValueError(f"Not a mailto URL: {mailto_url}")

        # Split recipient and query string
        rest = mailto_url[7:]  # Remove 'mailto:' prefix
        recipient, _, query_string = rest.partition("?")
        recipient = unquote(recipient)

        # Parse query parameters
        params = parse_qs(query_string)
        subject = unquote(params["subject"][0]) if params.get("subject") else None
        body = unquote(params["body"][0]) if params.get("body") else None

        return recipient, subject, body

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
            method_used=UnsubscribeMethod.MAILTO,
            status=UnsubscribeStatus.FAILED,
            timestamp=datetime.now(),
            error_message=error_message,
            details=details or {},
        )
