"""URL validation to prevent SSRF attacks."""

import ipaddress
from urllib.parse import urlparse


def is_safe_url(url: str) -> tuple[bool, str | None]:
    """
    Validate that a URL is safe to request (not targeting internal resources).

    Returns:
        Tuple of (is_safe, error_message)
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Must be HTTPS
    if parsed.scheme != "https":
        return False, f"URL must use HTTPS, got: {parsed.scheme}"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    # Block localhost and loopback
    if hostname in ("localhost", "127.0.0.1", "::1"):
        return False, "Cannot target localhost"

    # Check if hostname is an IP address
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private:
            return False, "Cannot target private IP addresses"
        if ip.is_loopback:
            return False, "Cannot target loopback addresses"
        if ip.is_link_local:
            return False, "Cannot target link-local addresses"
        if ip.is_reserved:
            return False, "Cannot target reserved IP addresses"
    except ValueError:
        # Not an IP address, it's a domain name - that's fine
        pass

    # Block common internal/cloud metadata hostnames
    blocked_hostnames = {
        "metadata.google.internal",
        "metadata.google",
        "169.254.169.254",  # AWS/GCP metadata
        "100.100.100.200",  # Alibaba metadata
    }
    if hostname.lower() in blocked_hostnames:
        return False, "Cannot target cloud metadata endpoints"

    return True, None
