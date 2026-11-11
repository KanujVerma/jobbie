from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING

from src.models import Job
from src.http import HTTPClient

if TYPE_CHECKING:
    from src.browser import BrowserClient


class BaseAdapter(ABC):
    source_platform: str  # class-level constant, e.g. "workday"

    # Declared by the adapter class, not by per-company config. An adapter that
    # touches self.browser must set this True: the config flag it replaces
    # (config.use_playwright) is opt-in per company, so an adapter needing a
    # browser whose config omits the flag silently receives browser=None.
    requires_browser: bool = False

    def __init__(self, company: str, config: dict, http: HTTPClient, browser: "BrowserClient | None" = None):
        self.company = company
        self.config = config
        self.http = http
        self.browser = browser
        # Some legacy adapters make several independent queries. Keep useful
        # partial observations, but never report those scans as healthy.
        self.fetch_errors: list[str] = []

    def record_fetch_error(self, error: Exception | str) -> None:
        """Expose a failed query without retaining response bodies or URLs."""
        response = getattr(error, "response", None)
        status = getattr(response, "status_code", None)
        label = f"HTTP {status}" if isinstance(status, int) else (
            type(error).__name__ if isinstance(error, Exception) else error
        )
        if label not in self.fetch_errors:
            self.fetch_errors.append(label)

    @abstractmethod
    def fetch(self) -> Iterator[Job]:
        """
        Yield normalized Job objects.
        - Set role_type hint if this is a known intern-only source.
        - Include official job ID if source provides one.
        - Populate raw_text from public source evidence; bounded detail fallbacks allowed.
        - Source failures should propagate to the caller for failed-vs-empty health.
        - Multi-query adapters may record_fetch_error and retain partial results.
        """
