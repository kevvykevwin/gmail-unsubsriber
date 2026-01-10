"""Data models for email subscriptions and unsubscribe results."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UnsubscribeMethod(str, Enum):
    """Method used for unsubscribing."""

    ONE_CLICK_HTTP = "one_click_http"
    MAILTO = "mailto"
    BROWSER = "browser"
    MARK_SPAM = "mark_spam"
    NOT_POSSIBLE = "not_possible"


class UnsubscribeStatus(str, Enum):
    """Status of an unsubscribe attempt."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Subscription(BaseModel):
    """A detected email subscription/mailing list."""

    sender_email: EmailStr
    sender_name: str
    sender_domain: str
    list_unsubscribe_url: str | None = None
    list_unsubscribe_mailto: str | None = None
    supports_one_click: bool = False
    message_count: int = 1
    sample_subjects: list[str] = Field(default_factory=list)
    first_seen: datetime
    last_seen: datetime
    message_ids: list[str] = Field(default_factory=list)

    @property
    def best_unsubscribe_method(self) -> UnsubscribeMethod:
        """Determine the best available unsubscribe method."""
        if self.supports_one_click and self.list_unsubscribe_url:
            return UnsubscribeMethod.ONE_CLICK_HTTP
        if self.list_unsubscribe_mailto:
            return UnsubscribeMethod.MAILTO
        if self.list_unsubscribe_url:
            return UnsubscribeMethod.BROWSER
        return UnsubscribeMethod.MARK_SPAM


class UnsubscribeResult(BaseModel):
    """Result of an unsubscribe attempt."""

    sender_email: EmailStr
    sender_name: str
    method_used: UnsubscribeMethod
    status: UnsubscribeStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: str | None = None
    details: dict = Field(default_factory=dict)


class ScanResult(BaseModel):
    """Result of a scan operation."""

    subscriptions: list[Subscription]
    total_messages_scanned: int
    scan_timestamp: datetime = Field(default_factory=datetime.now)
    scan_days: int
