"""Custom exceptions for the Gmail Unsubscribe Agent."""


class GmailUnsubError(Exception):
    """Base exception for Gmail Unsubscribe Agent."""

    pass


class AuthenticationError(GmailUnsubError):
    """OAuth authentication failed."""

    pass


class RateLimitExceededError(GmailUnsubError):
    """Gmail API rate limit exceeded after retries."""

    pass


class UnsubscribeFailedError(GmailUnsubError):
    """Unsubscribe attempt failed."""

    def __init__(
        self,
        message: str,
        method: str,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.method = method
        self.details = details or {}


class BrowserAutomationError(GmailUnsubError):
    """Playwright browser automation failed."""

    pass
