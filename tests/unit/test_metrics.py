"""Unit tests for RunMetrics and BaseMetricsCollectorMixin."""
from __future__ import annotations

import time

from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics


def test_run_metrics_to_dict_contains_all_fields():
    metrics = RunMetrics(method="baseline", model_name="test-model", precision_or_quant="fp32",
                          prompt_tokens=10, max_new_tokens=20)
    data = metrics.to_dict()
    assert data["method"] == "baseline"
    assert data["succeeded"] is True
    assert "timestamp" in data


class _Collector(BaseMetricsCollectorMixin):
    pass


def test_ram_sampling_captures_positive_peak():
    collector = _Collector()
    collector._sample_interval_sec = 0.01
    collector._start_ram_sampling()
    time.sleep(0.05)
    peak = collector._stop_ram_sampling()
    assert peak > 0


def test_ram_sampling_external_process_matches_current_process_by_name():
    # Sample this very test process by (part of) its own executable name — proves the
    # external-process code path (used by QuantizationService for the Ollama runner)
    # actually finds and measures a real OS process, not just self.
    import psutil

    own_name = psutil.Process().name()  # e.g. "python.exe" / "python"
    name_fragment = own_name.split(".")[0][:4]

    collector = _Collector()
    collector._external_sample_interval_sec = 0.01
    collector._start_ram_sampling(process_name_filter=name_fragment)
    # A single psutil.process_iter() pass over every OS process can take well over a
    # second on a machine with hundreds of running processes (measured ~1.4s on this
    # dev box) -- poll instead of a fixed short sleep to avoid flakiness across machines.
    deadline = time.monotonic() + 10.0
    while collector._peak_rss_mb == 0.0 and time.monotonic() < deadline:
        time.sleep(0.1)
    peak = collector._stop_ram_sampling()
    assert peak > 0


def test_ram_sampling_external_process_not_found_stays_zero():
    collector = _Collector()
    collector._external_sample_interval_sec = 0.01
    collector._start_ram_sampling(process_name_filter="definitely-not-a-real-process-xyz")
    time.sleep(0.05)
    peak = collector._stop_ram_sampling()
    assert peak == 0.0
