"""Email scanner for finding subscription emails."""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta

from gmail_unsub.gmail.client import GmailClient
from gmail_unsub.gmail.models import ScanResult, Subscription
from gmail_unsub.utils.patterns import (
    check_one_click_support,
    extract_domain,
    extract_sender_info,
    normalize_sender_key,
    parse_list_unsubscribe_header,
)


class EmailScanner:
    """Scan Gmail for subscription/marketing emails."""

    def __init__(self, client: GmailClient) -> None:
        self.client = client

    def scan(
        self,
        days_back: int = 90,
        max_emails: int = 1000,
        batch_size: int = 100,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ScanResult:
        """
        Scan inbox for subscription emails.

        Args:
            days_back: Number of days to scan back
            max_emails: Maximum emails to scan
            batch_size: Number of emails per API request
            progress_callback: Optional callback for progress updates (current, total)

        Returns:
            ScanResult with aggregated subscriptions
        """
        # Build search query
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        query = f"after:{since_date} (category:promotions OR category:updates)"

        # Collect all message IDs
        message_ids: list[str] = []
        page_token = None

        while len(message_ids) < max_emails:
            remaining = max_emails - len(message_ids)
            result = self.client.list_messages(
                query=query,
                max_results=min(batch_size, remaining),
                page_token=page_token,
            )

            messages = result.get("messages", [])
            if not messages:
                break

            message_ids.extend(msg["id"] for msg in messages)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        # Aggregate by sender
        subscriptions_map: dict[str, dict] = defaultdict(
            lambda: {
                "sender_email": "",
                "sender_name": "",
                "sender_domain": "",
                "list_unsubscribe_url": None,
                "list_unsubscribe_mailto": None,
                "supports_one_click": False,
                "message_count": 0,
                "sample_subjects": [],
                "first_seen": None,
                "last_seen": None,
                "message_ids": [],
            }
        )

        total = len(message_ids)
        for i, message_id in enumerate(message_ids):
            if progress_callback:
                progress_callback(i + 1, total)

            try:
                msg = self.client.get_message(message_id)
                self._process_message(msg, subscriptions_map)
            except Exception:
                # Skip messages that fail to process
                continue

        # Convert to Subscription objects (skip empty entries)
        subscriptions = [
            Subscription(
                sender_email=data["sender_email"],
                sender_name=data["sender_name"],
                sender_domain=data["sender_domain"],
                list_unsubscribe_url=data["list_unsubscribe_url"],
                list_unsubscribe_mailto=data["list_unsubscribe_mailto"],
                supports_one_click=data["supports_one_click"],
                message_count=data["message_count"],
                sample_subjects=data["sample_subjects"][:3],  # Keep top 3
                first_seen=data["first_seen"],
                last_seen=data["last_seen"],
                message_ids=data["message_ids"],
            )
            for data in subscriptions_map.values()
            if data["sender_email"]
        ]

        # Sort by message count (most frequent first)
        subscriptions.sort(key=lambda s: s.message_count, reverse=True)

        return ScanResult(
            subscriptions=subscriptions,
            total_messages_scanned=total,
            scan_days=days_back,
        )

    def _process_message(
        self,
        msg: dict,
        subscriptions_map: dict[str, dict],
    ) -> None:
        """Process a single message and update the subscriptions map."""
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        from_header = headers.get("From", "")
        if not from_header:
            return

        sender_name, sender_email = extract_sender_info(from_header)
        sender_key = normalize_sender_key(sender_email)

        # Parse unsubscribe headers
        list_unsub = headers.get("List-Unsubscribe", "")
        list_unsub_post = headers.get("List-Unsubscribe-Post", "")

        http_url, mailto_url, _ = parse_list_unsubscribe_header(list_unsub)
        supports_one_click = check_one_click_support(list_unsub_post)

        # Skip if no unsubscribe mechanism
        if not http_url and not mailto_url:
            return

        # Parse date (defaults to now if parsing fails)
        date_str = headers.get("Date", "")
        try:
            msg_date = self._parse_date(date_str)
        except Exception:
            msg_date = datetime.now()

        # Update subscription data
        sub = subscriptions_map[sender_key]
        sub["sender_email"] = sender_email
        sub["sender_name"] = sender_name
        sub["sender_domain"] = extract_domain(sender_email)
        sub["message_count"] += 1
        sub["message_ids"].append(msg["id"])

        # Keep the most recent unsubscribe URL
        if http_url:
            sub["list_unsubscribe_url"] = http_url
        if mailto_url:
            sub["list_unsubscribe_mailto"] = mailto_url
        if supports_one_click:
            sub["supports_one_click"] = True

        # Track subjects (for display)
        subject = headers.get("Subject", "(no subject)")
        if subject not in sub["sample_subjects"]:
            sub["sample_subjects"].append(subject)

        # Track date range
        if sub["first_seen"] is None or msg_date < sub["first_seen"]:
            sub["first_seen"] = msg_date
        if sub["last_seen"] is None or msg_date > sub["last_seen"]:
            sub["last_seen"] = msg_date

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date header."""
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(date_str) if date_str else datetime.now()
