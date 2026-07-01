"""Unit tests for AirllmService (layer-by-layer execution path)."""
from __future__ import annotations

import sys

from local_llm_bench.services.airllm_service import AirllmService
from local_llm_bench.shared.gatekeeper import ApiGatekeeper


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper({"requests_per_minute": 100, "max_retries": 1, "retry_after_seconds": 0})


def test_run_returns_successful_metrics(fake_ml_stack):
    service = AirllmService(_gatekeeper())
    metrics = service.run("fake/model", "fp16", "hello", 20)
    assert metrics.succeeded is True
    assert metrics.method == "airllm"
    assert metrics.generated_text == "generated text"


def test_run_handles_load_failure_gracefully(fake_ml_stack):
    sys.modules["airllm"].AutoModel.from_pretrained.side_effect = RuntimeError("disk I/O error")
    service = AirllmService(_gatekeeper())
    metrics = service.run("fake/model", "fp16", "hello", 20)
    assert metrics.succeeded is False
    assert metrics.error is not None
