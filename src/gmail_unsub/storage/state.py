"""State persistence for tracking processed emails."""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from gmail_unsub.gmail.models import ScanResult, Subscription


class ProcessedEmail(BaseModel):
    """Record of a processed email."""

    message_id: str
    sender: str
    processed_at: datetime
    action: str


class StateManager:
    """Manage state persistence for processed emails and scan results."""

    def __init__(self, state_file: Path, scan_results_file: Path) -> None:
        self.state_file = state_file
        self.scan_results_file = scan_results_file
        self._state: dict[str, ProcessedEmail] = {}
        self._load()

    def _load(self) -> None:
        """Load state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self._state = {k: ProcessedEmail(**v) for k, v in data.items()}
            except Exception:
                self._state = {}

    def save(self) -> None:
        """Save state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(
                {k: v.model_dump(mode="json") for k, v in self._state.items()},
                indent=2,
                default=str,
            )
        )

    def is_processed(self, message_id: str) -> bool:
        """Check if a message has been processed."""
        return message_id in self._state

    def mark_processed(self, email: ProcessedEmail) -> None:
        """Mark an email as processed."""
        self._state[email.message_id] = email
        self.save()

    def get_processed_senders(self) -> set[str]:
        """Get set of all processed senders."""
        return {e.sender for e in self._state.values()}

    def clear(self) -> None:
        """Clear all state."""
        self._state = {}
        if self.state_file.exists():
            self.state_file.unlink()

    # Scan results caching

    def save_scan_results(self, results: ScanResult) -> None:
        """Cache scan results for later selection."""
        self.scan_results_file.parent.mkdir(parents=True, exist_ok=True)
        self.scan_results_file.write_text(
            results.model_dump_json(indent=2),
        )

    def load_scan_results(self) -> ScanResult | None:
        """Load cached scan results."""
        if not self.scan_results_file.exists():
            return None
        try:
            data = json.loads(self.scan_results_file.read_text())
            return ScanResult(**data)
        except Exception:
            return None

    def has_scan_results(self) -> bool:
        """Check if scan results are cached."""
        return self.scan_results_file.exists()

    def get_subscription_by_email(self, sender_email: str) -> Subscription | None:
        """Get a subscription from cached results by email."""
        results = self.load_scan_results()
        if not results:
            return None

        # Find matching subscription
        return next(
            (sub for sub in results.subscriptions if sub.sender_email == sender_email),
            None,
        )

    def clear_scan_results(self) -> None:
        """Clear cached scan results."""
        if self.scan_results_file.exists():
            self.scan_results_file.unlink()
