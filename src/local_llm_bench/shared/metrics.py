"""Shared metrics data model and background RAM-sampling mixin.

Reused by every execution service (baseline/AirLLM/quantized) so peak-RAM measurement
logic exists in exactly one place instead of being duplicated three times.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class RunMetrics:
    """Unified result record produced by every execution method, for apples-to-apples comparison."""

    method: str
    model_name: str
    precision_or_quant: str
    prompt_tokens: int
    max_new_tokens: int
    succeeded: bool = True
    error: str | None = None
    load_time_sec: float = 0.0
    ttft_sec: float = 0.0
    """Time To First Token — measures the Prefill stage (KV cache build + first-token compute)."""
    tpot_sec: float = 0.0
    """Time Per Output Token, averaged — measures the Decode stage (a.k.a. Inter-Token Latency)."""
    tokens_per_sec: float = 0.0
    peak_ram_mb: float = 0.0
    total_wall_time_sec: float = 0.0
    estimated_power_wh: float = 0.0
    """Estimated (not measured) energy use: configured assumed TDP watts x wall time."""
    generated_text: str = ""
    quality_note: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class BaseMetricsCollectorMixin:
    """Samples this process's RSS memory on a background thread to capture true peak usage.

    A single end-of-run reading misses the actual peak, which usually occurs mid-load —
    sampling continuously is the only reliable way to measure it.
    """

    _sample_interval_sec: float = 0.05

    def _start_ram_sampling(self) -> None:
        self._peak_rss_mb = 0.0
        self._sampling = True
        self._sampler_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._sampler_thread.start()

    def _sample_loop(self) -> None:
        import psutil

        process = psutil.Process()
        while self._sampling:
            rss_mb = process.memory_info().rss / (1024 * 1024)
            if rss_mb > self._peak_rss_mb:
                self._peak_rss_mb = rss_mb
            time.sleep(self._sample_interval_sec)

    def _stop_ram_sampling(self) -> float:
        self._sampling = False
        self._sampler_thread.join(timeout=1.0)
        return self._peak_rss_mb
