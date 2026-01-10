"""Gmail API client wrapper with rate limiting."""

import base64
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from gmail_unsub.utils.rate_limiter import RateLimiter


class GmailClient:
    """Wrapper for Gmail API with rate limiting."""

    SPAM_LABEL_ID = "SPAM"

    def __init__(self, credentials: Credentials, rate_limiter: RateLimiter) -> None:
        self.service = build("gmail", "v1", credentials=credentials)
        self.rate_limiter = rate_limiter

    def list_messages(
        self,
        query: str,
        max_results: int = 100,
        page_token: str | None = None,
    ) -> dict:
        """List messages matching query with rate limiting."""
        with self.rate_limiter:
            result = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=max_results,
                    pageToken=page_token,
                )
                .execute()
            )
        return result

    def get_message(
        self,
        message_id: str,
        format: str = "metadata",
    ) -> dict:
        """Get a specific message with headers."""
        with self.rate_limiter:
            result = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format=format,
                    metadataHeaders=[
                        "From",
                        "Subject",
                        "Date",
                        "List-Unsubscribe",
                        "List-Unsubscribe-Post",
                    ],
                )
                .execute()
            )
        return result

    def modify_labels(
        self,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict:
        """Add or remove labels from a message."""
        with self.rate_limiter:
            result = (
                self.service.users()
                .messages()
                .modify(
                    userId="me",
                    id=message_id,
                    body={
                        "addLabelIds": add_labels or [],
                        "removeLabelIds": remove_labels or [],
                    },
                )
                .execute()
            )
        return result

    def mark_as_spam(self, message_ids: list[str]) -> None:
        """Mark messages as spam by moving from inbox to spam."""
        for message_id in message_ids:
            self.modify_labels(
                message_id,
                add_labels=[self.SPAM_LABEL_ID],
                remove_labels=["INBOX"],
            )

    def remove_from_spam(self, message_ids: list[str]) -> None:
        """Remove messages from spam by moving back to inbox."""
        for message_id in message_ids:
            self.modify_labels(
                message_id,
                add_labels=["INBOX"],
                remove_labels=[self.SPAM_LABEL_ID],
            )

    def send_message(self, to: str, subject: str, body: str) -> dict:
        """Send an email message (used for mailto: unsubscribe)."""
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        with self.rate_limiter:
            result = (
                self.service.users()
                .messages()
                .send(
                    userId="me",
                    body={"raw": raw},
                )
                .execute()
            )
        return result

    def batch_get_messages(
        self,
        message_ids: list[str],
        format: str = "metadata",
    ) -> list[dict]:
        """Get multiple messages (no native batch, so sequential with rate limiting)."""
        messages = []
        for message_id in message_ids:
            try:
                msg = self.get_message(message_id, format=format)
                messages.append(msg)
            except Exception:
                # Skip messages that fail to fetch
                continue
        return messages
