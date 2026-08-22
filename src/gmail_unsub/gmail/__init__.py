"""Gmail API client and email scanning."""

from gmail_unsub.gmail.client import GmailClient
from gmail_unsub.gmail.models import (
    Subscription,
    UnsubscribeMethod,
    UnsubscribeResult,
    UnsubscribeStatus,
)
from gmail_unsub.gmail.scanner import EmailScanner

__all__ = [
    "GmailClient",
    "EmailScanner",
    "Subscription",
    "UnsubscribeMethod",
    "UnsubscribeResult",
    "UnsubscribeStatus",
]
