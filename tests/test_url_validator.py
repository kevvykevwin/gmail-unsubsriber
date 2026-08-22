"""Tests for URL validation to prevent SSRF attacks."""


from gmail_unsub.utils.url_validator import is_safe_url


class TestIsSafeUrl:
    def test_valid_https_url(self):
        is_safe, error = is_safe_url("https://example.com/unsubscribe")
        assert is_safe is True
        assert error is None

    def test_rejects_http(self):
        is_safe, error = is_safe_url("http://example.com/unsubscribe")
        assert is_safe is False
        assert "HTTPS" in error

    def test_rejects_localhost(self):
        is_safe, error = is_safe_url("https://localhost/admin")
        assert is_safe is False
        assert "localhost" in error

    def test_rejects_127_0_0_1(self):
        is_safe, error = is_safe_url("https://127.0.0.1/internal")
        assert is_safe is False
        assert "localhost" in error

    def test_rejects_private_ip_10(self):
        is_safe, error = is_safe_url("https://10.0.0.1/internal")
        assert is_safe is False
        assert "private" in error.lower()

    def test_rejects_private_ip_172(self):
        is_safe, error = is_safe_url("https://172.16.0.1/internal")
        assert is_safe is False
        assert "private" in error.lower()

    def test_rejects_private_ip_192(self):
        is_safe, error = is_safe_url("https://192.168.1.1/router")
        assert is_safe is False
        assert "private" in error.lower()

    def test_rejects_aws_metadata(self):
        is_safe, error = is_safe_url("https://169.254.169.254/latest/meta-data/")
        assert is_safe is False
        # 169.254.x.x is link-local but also in blocked hostnames list
        assert error is not None

    def test_allows_public_ip(self):
        is_safe, error = is_safe_url("https://8.8.8.8/test")
        assert is_safe is True
        assert error is None

    def test_allows_domain_name(self):
        is_safe, error = is_safe_url("https://newsletter.example.com/unsubscribe?token=abc")
        assert is_safe is True
        assert error is None

    def test_rejects_no_hostname(self):
        is_safe, error = is_safe_url("https:///path")
        assert is_safe is False
        assert "hostname" in error.lower()

    def test_rejects_invalid_url(self):
        is_safe, error = is_safe_url("not a url at all")
        assert is_safe is False
