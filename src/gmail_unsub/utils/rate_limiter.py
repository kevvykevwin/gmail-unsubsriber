"""Rate limiting with exponential backoff for Gmail API."""

import random
import time
from collections.abc import Callable
from typing import Literal, TypeVar

from googleapiclient.errors import HttpError

from gmail_unsub.utils.errors import RateLimitExceededError

T = TypeVar("T")


class RateLimiter:
    """Rate limiter with exponential backoff for API calls."""

    def __init__(
        self,
        requests_per_second: float = 10.0,
        max_retries: int = 5,
        base_backoff: float = 1.0,
    ) -> None:
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self.max_retries = max_retries
        self.base_backoff = base_backoff

    def wait(self) -> None:
        """Wait for the minimum interval since last request."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

    def __enter__(self) -> "RateLimiter":
        """Enter context manager - wait for rate limit."""
        self.wait()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> Literal[False]:
        """Exit context manager - no special handling needed."""
        return False

    def execute(self, func: Callable[[], T]) -> T:
        """Execute a callable with rate limiting and exponential backoff retry."""
        retries = 0

        while True:
            self.wait()
            try:
                return func()
            except HttpError as e:
                if e.resp.status in (429, 503):  # Rate limit or service unavailable
                    retries += 1
                    if retries > self.max_retries:
                        raise RateLimitExceededError(
                            f"Rate limit exceeded after {self.max_retries} retries"
                        ) from e

                    # Exponential backoff with jitter
                    backoff = self.base_backoff * (2**retries) + random.uniform(0, 1)
                    time.sleep(backoff)
                else:
                    raise
