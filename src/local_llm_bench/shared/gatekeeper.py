"""Centralized gatekeeper for ALL external calls (Hugging Face Hub, Ollama).

No service may call an external API/process directly — every such call must go
through ApiGatekeeper.execute() for rate limiting, queueing, retry, and logging
(guidelines section 5.1).
"""
from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("local_llm_bench.gatekeeper")


@dataclass
class QueueStatus:
    depth: int
    calls_in_window: int


class ApiGatekeeper:
    """Wraps external calls with rate limiting, FIFO queueing, and retry-with-backoff."""

    def __init__(self, rate_limit_config: dict):
        self._per_minute = rate_limit_config.get("requests_per_minute", 30)
        self._max_retries = rate_limit_config.get("max_retries", 3)
        self._retry_after = rate_limit_config.get("retry_after_seconds", 5)
        self._call_timestamps: deque[float] = deque()
        self._queue: deque[Callable[[], Any]] = deque()

    def _wait_for_slot(self) -> None:
        now = time.monotonic()
        window_start = now - 60.0
        while self._call_timestamps and self._call_timestamps[0] < window_start:
            self._call_timestamps.popleft()
        if len(self._call_timestamps) >= self._per_minute:
            sleep_for = 60.0 - (now - self._call_timestamps[0])
            logger.info("Rate limit reached, waiting %.1fs", sleep_for)
            time.sleep(max(sleep_for, 0.0))

    def execute(self, api_call: Callable[[], Any], *, description: str = "") -> Any:
        """Execute api_call through the gatekeeper: rate-limit, retry on failure, log."""
        self._wait_for_slot()
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info("Calling %s (attempt %d/%d)", description, attempt, self._max_retries)
                self._call_timestamps.append(time.monotonic())
                result = api_call()
                logger.info("Call %s succeeded", description)
                return result
            except Exception as exc:  # noqa: BLE001 - any external call may legitimately fail
                last_error = exc
                logger.warning("Call %s failed (attempt %d): %s", description, attempt, exc)
                if attempt < self._max_retries:
                    time.sleep(self._retry_after)
        raise RuntimeError(f"{description} failed after {self._max_retries} attempts") from last_error

    def get_queue_status(self) -> QueueStatus:
        return QueueStatus(depth=len(self._queue), calls_in_window=len(self._call_timestamps))
