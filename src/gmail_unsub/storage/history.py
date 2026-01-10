"""History tracking for unsubscribe actions."""

import csv
import json
from datetime import datetime
from pathlib import Path

from gmail_unsub.gmail.models import UnsubscribeMethod, UnsubscribeResult, UnsubscribeStatus


class HistoryTracker:
    """Track history of unsubscribe actions."""

    def __init__(self, history_file: Path) -> None:
        self.history_file = history_file
        self._history: list[UnsubscribeResult] = []
        self._load()

    def _load(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text())
                self._history = [UnsubscribeResult(**item) for item in data]
            except Exception:
                self._history = []

    def _save(self) -> None:
        """Save history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in self._history],
                indent=2,
                default=str,
            )
        )

    def record(self, result: UnsubscribeResult) -> None:
        """Record an unsubscribe result."""
        self._history.append(result)
        self._save()

    def get_history(
        self,
        status: UnsubscribeStatus | None = None,
        method: UnsubscribeMethod | None = None,
        limit: int = 100,
    ) -> list[UnsubscribeResult]:
        """Get history entries with optional filters."""
        filtered = self._history

        if status is not None:
            filtered = [r for r in filtered if r.status == status]

        if method is not None:
            filtered = [r for r in filtered if r.method_used == method]

        return filtered[-limit:]

    def get_by_sender(self, sender_email: str) -> list[UnsubscribeResult]:
        """Get all history entries for a specific sender."""
        return [r for r in self._history if r.sender_email == sender_email]

    def get_recent(self, days: int = 7) -> list[UnsubscribeResult]:
        """Get recent history entries."""
        seconds_in_day = 86400  # 24 * 60 * 60
        cutoff = datetime.now().timestamp() - (days * seconds_in_day)
        return [r for r in self._history if r.timestamp.timestamp() > cutoff]

    def get_stats(self) -> dict:
        """Get summary statistics."""
        total = len(self._history)
        if total == 0:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "by_method": {},
            }

        success = sum(1 for r in self._history if r.status == UnsubscribeStatus.SUCCESS)
        failed = sum(1 for r in self._history if r.status == UnsubscribeStatus.FAILED)

        by_method = {}
        for method in UnsubscribeMethod:
            count = sum(1 for r in self._history if r.method_used == method)
            if count > 0:
                by_method[method.value] = count

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": f"{(success / total) * 100:.1f}%",
            "by_method": by_method,
        }

    def export_csv(self, output_path: Path) -> None:
        """Export history to CSV for analysis."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["timestamp", "sender_email", "sender_name", "method", "status", "error"]
            )

            for result in self._history:
                writer.writerow(
                    [
                        result.timestamp.isoformat(),
                        result.sender_email,
                        result.sender_name,
                        result.method_used.value,
                        result.status.value,
                        result.error_message or "",
                    ]
                )

    def clear(self) -> None:
        """Clear all history."""
        self._history = []
        if self.history_file.exists():
            self.history_file.unlink()
