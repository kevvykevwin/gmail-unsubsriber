"""Utility modules."""

from gmail_unsub.utils.errors import (
    AuthenticationError,
    BrowserAutomationError,
    GmailUnsubError,
    RateLimitExceededError,
    UnsubscribeFailedError,
)
from gmail_unsub.utils.rate_limiter import RateLimiter
from gmail_unsub.utils.url_validator import is_safe_url

__all__ = [
    "RateLimiter",
    "GmailUnsubError",
    "AuthenticationError",
    "RateLimitExceededError",
    "UnsubscribeFailedError",
    "BrowserAutomationError",
    "is_safe_url",
]
