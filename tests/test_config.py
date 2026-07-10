"""Tests for application configuration validation."""

import pytest
from pydantic import ValidationError

from gmail_unsub.config import Settings


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_emails_to_scan", 0),
        ("scan_days_back", -1),
        ("batch_size", 0),
        ("api_requests_per_second", 0),
        ("max_retries", -1),
        ("base_backoff_seconds", -0.1),
        ("browser_timeout_ms", 0),
    ],
)
def test_rejects_invalid_numeric_settings(field, value):
    """Reject config values that would break scanner, retry, or browser behavior."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})


def test_allows_zero_retry_and_backoff_settings():
    """Allow explicit no-retry/no-backoff settings while keeping positive rate limits."""
    settings = Settings(
        _env_file=None,
        max_retries=0,
        base_backoff_seconds=0,
        api_requests_per_second=1,
    )

    assert settings.max_retries == 0
    assert settings.base_backoff_seconds == 0
    assert settings.api_requests_per_second == 1
