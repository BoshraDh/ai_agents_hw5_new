"""Unit tests for ModelLoaderService (baseline execution path)."""
from __future__ import annotations

import sys

import pytest

from local_llm_bench.services.model_loader_service import ModelLoaderService
from local_llm_bench.shared.gatekeeper import ApiGatekeeper


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper({"requests_per_minute": 100, "max_retries": 1, "retry_after_seconds": 0})


def test_run_returns_successful_metrics(fake_ml_stack):
    service = ModelLoaderService(_gatekeeper())
    metrics = service.run("fake/model", "fp32", "hello", 20)
    assert metrics.succeeded is True
    assert metrics.method == "baseline"
    assert metrics.tokens_per_sec >= 0
    assert metrics.generated_text == "generated text"


def test_run_rejects_unsupported_precision_fail_fast(fake_ml_stack):
    service = ModelLoaderService(_gatekeeper())
    with pytest.raises(ValueError, match="Unsupported precision"):
        service.run("fake/model", "int8", "hello", 20)


def test_run_handles_model_load_failure_gracefully(fake_ml_stack):
    sys.modules["transformers"].AutoModelForCausalLM.from_pretrained.side_effect = MemoryError("OOM")
    service = ModelLoaderService(_gatekeeper())
    metrics = service.run("fake/model", "fp32", "hello", 20)
    assert metrics.succeeded is False
    assert metrics.error is not None
