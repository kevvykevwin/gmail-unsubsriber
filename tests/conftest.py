"""Pytest fixtures for Gmail Unsubscribe Agent tests."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from gmail_unsub.gmail.models import Subscription


@pytest.fixture
def mock_gmail_service():
    """Mock Gmail API service for unit tests."""
    service = MagicMock()

    # Mock messages().list()
    service.users().messages().list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ],
        "nextPageToken": None,
    }

    # Mock messages().get()
    service.users().messages().get.return_value.execute.return_value = {
        "id": "msg1",
        "payload": {
            "headers": [
                {"name": "From", "value": "Newsletter <news@example.com>"},
                {"name": "Subject", "value": "Weekly Update"},
                {"name": "List-Unsubscribe", "value": "<https://example.com/unsub>"},
                {"name": "List-Unsubscribe-Post", "value": "List-Unsubscribe=One-Click"},
            ]
        },
    }

    return service


@pytest.fixture
def sample_subscription():
    """Sample subscription for testing."""
    return Subscription(
        sender_email="news@example.com",
        sender_name="Example Newsletter",
        sender_domain="example.com",
        list_unsubscribe_url="https://example.com/unsub/123",
        list_unsubscribe_mailto="mailto:unsub@example.com",
        supports_one_click=True,
        message_count=5,
        sample_subjects=["Weekly Update", "Monthly Digest"],
        first_seen=datetime(2024, 1, 1),
        last_seen=datetime(2024, 1, 15),
        message_ids=["msg1", "msg2", "msg3", "msg4", "msg5"],
    )


@pytest.fixture
def subscription_mailto_only():
    """Subscription with only mailto unsubscribe."""
    return Subscription(
        sender_email="promo@shop.com",
        sender_name="Shop Promotions",
        sender_domain="shop.com",
        list_unsubscribe_url=None,
        list_unsubscribe_mailto="mailto:unsub@shop.com?subject=Unsubscribe",
        supports_one_click=False,
        message_count=10,
        sample_subjects=["50% Off Sale!"],
        first_seen=datetime(2024, 1, 1),
        last_seen=datetime(2024, 1, 20),
        message_ids=["msg10"],
    )


@pytest.fixture
def subscription_browser_only():
    """Subscription requiring browser automation."""
    return Subscription(
        sender_email="alerts@service.io",
        sender_name="Service Alerts",
        sender_domain="service.io",
        list_unsubscribe_url="https://service.io/preferences/email",
        list_unsubscribe_mailto=None,
        supports_one_click=False,
        message_count=3,
        sample_subjects=["Alert: New Activity"],
        first_seen=datetime(2024, 1, 5),
        last_seen=datetime(2024, 1, 18),
        message_ids=["msg20"],
    )
