"""Email pattern detection for identifying marketing/subscription emails."""

import re

# Known marketing/email service provider domains
MARKETING_DOMAINS = frozenset([
    "mailchimp.com",
    "sendgrid.net",
    "amazonaws.com",
    "constantcontact.com",
    "hubspot.com",
    "klaviyo.com",
    "sailthru.com",
    "braze.com",
    "iterable.com",
    "customer.io",
    "mailgun.org",
    "postmarkapp.com",
    "sparkpost.com",
    "sendinblue.com",
    "campaignmonitor.com",
    "getresponse.com",
    "convertkit.com",
    "drip.com",
    "activecampaign.com",
    "mailerlite.com",
    "beehiiv.com",
    "substack.com",
])

# Keywords suggesting subscription/marketing emails
SUBSCRIPTION_KEYWORDS = frozenset([
    "newsletter",
    "digest",
    "weekly",
    "monthly",
    "daily",
    "updates",
    "noreply",
    "no-reply",
    "donotreply",
    "marketing",
    "promo",
    "promotion",
    "offer",
    "discount",
    "subscribe",
    "unsubscribe",
    "notification",
    "alert",
])


def parse_list_unsubscribe_header(header_value: str) -> tuple[str | None, str | None, bool]:
    """
    Parse List-Unsubscribe header value.

    Returns:
        Tuple of (http_url, mailto_url, supports_one_click)
    """
    if not header_value:
        return None, None, False

    http_url = None
    mailto_url = None

    # Extract URLs from angle brackets: <https://...>, <mailto:...>
    matches = re.findall(r"<([^>]+)>", header_value)
    for match in matches:
        if match.startswith("http://") or match.startswith("https://"):
            http_url = match
        elif match.startswith("mailto:"):
            mailto_url = match

    return http_url, mailto_url, False  # one_click determined by List-Unsubscribe-Post


def check_one_click_support(list_unsubscribe_post: str | None) -> bool:
    """Check if List-Unsubscribe-Post header indicates one-click support."""
    if not list_unsubscribe_post:
        return False
    return "List-Unsubscribe=One-Click" in list_unsubscribe_post


def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@")[-1].lower()
    return ""


def extract_sender_info(from_header: str) -> tuple[str, str]:
    """
    Extract sender name and email from From header.

    Returns:
        Tuple of (sender_name, sender_email)
    """
    # Handle format: "Name" <email@example.com>
    match = re.match(r'^"?([^"<]*)"?\s*<([^>]+)>', from_header)
    if match:
        name = match.group(1).strip()
        email = match.group(2).strip().lower()
        return name or email, email

    # Handle format: email@example.com
    match = re.match(r"^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$", from_header.strip())
    if match:
        email = match.group(1).lower()
        return email, email

    # Fallback
    return from_header.strip(), from_header.strip()


def is_marketing_sender(sender_email: str) -> bool:
    """Check if sender appears to be from a marketing/email service."""
    domain = extract_domain(sender_email)

    # Check against known marketing domains
    if any(domain.endswith(md) for md in MARKETING_DOMAINS):
        return True

    # Check for subscription keywords in email
    email_lower = sender_email.lower()
    return any(keyword in email_lower for keyword in SUBSCRIPTION_KEYWORDS)


def normalize_sender_key(sender_email: str) -> str:
    """Normalize sender email for deduplication."""
    # Remove +suffixes (e.g., user+tag@example.com -> user@example.com)
    if "+" in sender_email:
        local, domain = sender_email.rsplit("@", 1)
        local = local.split("+")[0]
        return f"{local}@{domain}".lower()
    return sender_email.lower()
