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
    """Samples process RSS memory on a background thread to capture true peak usage.

    A single end-of-run reading misses the actual peak, which usually occurs mid-load —
    sampling continuously is the only reliable way to measure it.

    By default samples this Python process itself (correct for ModelLoaderService and
    AirllmService, which load weights in-process). QuantizationService instead passes
    process_name_filter="llama-server" / "ollama_llama_server", because Ollama loads the
    model in a *separate* OS process — sampling our own process there would silently
    measure the lightweight HTTP client instead of the actual model runner (this exact
    mistake was made and caught during Phase 4 execution: it originally reported ~36MB
    peak RAM for a 7.9GB quantized model).
    """

    _sample_interval_sec: float = 0.05
    _external_sample_interval_sec: float = 0.5

    def _start_ram_sampling(self, process_name_filter: str | None = None) -> None:
        self._peak_rss_mb = 0.0
        self._sampling = True
        self._process_name_filter = process_name_filter
        self._sampler_thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._sampler_thread.start()

    def _sample_loop(self) -> None:
        import psutil

        if self._process_name_filter:
            self._sample_loop_external(psutil)
        else:
            self._sample_loop_self(psutil)

    def _sample_loop_self(self, psutil) -> None:  # noqa: ANN001
        process = psutil.Process()
        while self._sampling:
            rss_mb = process.memory_info().rss / (1024 * 1024)
            if rss_mb > self._peak_rss_mb:
                self._peak_rss_mb = rss_mb
            time.sleep(self._sample_interval_sec)

    def _sample_loop_external(self, psutil) -> None:  # noqa: ANN001
        name_filter = self._process_name_filter.lower()
        while self._sampling:
            for proc in psutil.process_iter(["name", "memory_info"]):
                try:
                    if name_filter in (proc.info["name"] or "").lower():
                        rss_mb = proc.info["memory_info"].rss / (1024 * 1024)
                        if rss_mb > self._peak_rss_mb:
                            self._peak_rss_mb = rss_mb
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            time.sleep(self._external_sample_interval_sec)

    def _stop_ram_sampling(self) -> float:
        self._sampling = False
        # A single external process_iter() pass can exceed 1s on a busy machine (see
        # tests/unit/test_metrics.py) -- use a generous timeout so we don't return before
        # the in-flight sample finishes.
        self._sampler_thread.join(timeout=3.0)
        return self._peak_rss_mb
