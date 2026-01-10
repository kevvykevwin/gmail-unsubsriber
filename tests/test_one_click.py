"""Tests for RFC 8058 one-click unsubscribe handler."""

import pytest
from unittest.mock import AsyncMock, patch

from gmail_unsub.gmail.models import UnsubscribeMethod, UnsubscribeStatus
from gmail_unsub.unsubscribe.one_click import OneClickHandler


class TestOneClickHandler:
    @pytest.fixture
    def handler(self):
        return OneClickHandler(timeout=10)

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self, handler, sample_subscription):
        """Test successful one-click unsubscribe."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = await handler.unsubscribe(sample_subscription)

            assert result.status == UnsubscribeStatus.SUCCESS
            assert result.method_used == UnsubscribeMethod.ONE_CLICK_HTTP

    @pytest.mark.asyncio
    async def test_unsubscribe_not_supported(self, handler, subscription_browser_only):
        """Test when one-click is not supported."""
        result = await handler.unsubscribe(subscription_browser_only)

        assert result.status == UnsubscribeStatus.FAILED
        assert "not supported" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_rejects_http_url(self, handler, sample_subscription):
        """Test that HTTP (non-HTTPS) URLs are rejected."""
        sample_subscription.list_unsubscribe_url = "http://example.com/unsub"

        result = await handler.unsubscribe(sample_subscription)

        assert result.status == UnsubscribeStatus.FAILED
        assert "https" in result.error_message.lower()
