"""Tests for email pattern detection utilities."""

import pytest

from gmail_unsub.utils.patterns import (
    check_one_click_support,
    extract_domain,
    extract_sender_info,
    is_marketing_sender,
    normalize_sender_key,
    parse_list_unsubscribe_header,
)


class TestParseListUnsubscribeHeader:
    def test_parse_https_url(self):
        header = "<https://example.com/unsub/123>"
        http_url, mailto, _ = parse_list_unsubscribe_header(header)
        assert http_url == "https://example.com/unsub/123"
        assert mailto is None

    def test_parse_mailto(self):
        header = "<mailto:unsub@example.com>"
        http_url, mailto, _ = parse_list_unsubscribe_header(header)
        assert http_url is None
        assert mailto == "mailto:unsub@example.com"

    def test_parse_both(self):
        header = "<https://example.com/unsub>, <mailto:unsub@example.com>"
        http_url, mailto, _ = parse_list_unsubscribe_header(header)
        assert http_url == "https://example.com/unsub"
        assert mailto == "mailto:unsub@example.com"

    def test_parse_empty(self):
        http_url, mailto, _ = parse_list_unsubscribe_header("")
        assert http_url is None
        assert mailto is None


class TestCheckOneClickSupport:
    def test_one_click_supported(self):
        assert check_one_click_support("List-Unsubscribe=One-Click") is True

    def test_one_click_not_supported(self):
        assert check_one_click_support("") is False
        assert check_one_click_support(None) is False
        assert check_one_click_support("something-else") is False


class TestExtractDomain:
    def test_simple_email(self):
        assert extract_domain("user@example.com") == "example.com"

    def test_subdomain(self):
        assert extract_domain("user@mail.example.com") == "mail.example.com"

    def test_no_at_sign(self):
        assert extract_domain("invalid") == ""


class TestExtractSenderInfo:
    def test_name_and_email(self):
        name, email = extract_sender_info('"Newsletter" <news@example.com>')
        assert name == "Newsletter"
        assert email == "news@example.com"

    def test_name_without_quotes(self):
        name, email = extract_sender_info("Newsletter <news@example.com>")
        assert name == "Newsletter"
        assert email == "news@example.com"

    def test_email_only(self):
        name, email = extract_sender_info("news@example.com")
        assert name == "news@example.com"
        assert email == "news@example.com"


class TestIsMarketingSender:
    def test_known_marketing_domain(self):
        assert is_marketing_sender("bounce@mail.mailchimp.com") is True
        assert is_marketing_sender("notify@sendgrid.net") is True

    def test_subscription_keyword(self):
        assert is_marketing_sender("newsletter@example.com") is True
        assert is_marketing_sender("noreply@example.com") is True

    def test_regular_sender(self):
        assert is_marketing_sender("john@example.com") is False


class TestNormalizeSenderKey:
    def test_removes_plus_suffix(self):
        assert normalize_sender_key("user+tag@example.com") == "user@example.com"

    def test_lowercase(self):
        assert normalize_sender_key("User@Example.COM") == "user@example.com"

    def test_no_change_needed(self):
        assert normalize_sender_key("user@example.com") == "user@example.com"
