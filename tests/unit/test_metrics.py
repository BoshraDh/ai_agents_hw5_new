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
