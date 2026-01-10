"""Configuration management using Pydantic settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="GMAIL_UNSUB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # OAuth Configuration
    credentials_path: Path = Path("credentials.json")
    token_path: Path = Path("token.json")
    scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
    ]

    # Scanning Configuration
    max_emails_to_scan: int = 1000
    scan_days_back: int = 90
    batch_size: int = 100

    # Rate Limiting
    api_requests_per_second: float = 10.0
    max_retries: int = 5
    base_backoff_seconds: float = 1.0

    # Browser Automation
    browser_headless: bool = True
    browser_timeout_ms: int = 30000

    # Storage
    data_dir: Path = Path("data")

    @property
    def state_file(self) -> Path:
        """Path to state file."""
        return self.data_dir / "state.json"

    @property
    def history_file(self) -> Path:
        """Path to history file."""
        return self.data_dir / "history.json"

    @property
    def scan_results_file(self) -> Path:
        """Path to cached scan results."""
        return self.data_dir / "scan_results.json"


# Global settings instance
settings = Settings()
