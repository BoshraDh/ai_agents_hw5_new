"""Unit tests for QuantizationService (Ollama/GGUF execution path)."""
from __future__ import annotations

import pytest

from local_llm_bench.services.quantization_service import QuantizationService
from local_llm_bench.shared.gatekeeper import ApiGatekeeper


def _gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper({"requests_per_minute": 100, "max_retries": 1, "retry_after_seconds": 0})


def test_run_rejects_unsupported_quant_level():
    service = QuantizationService(_gatekeeper(), "http://localhost:11434")
    with pytest.raises(ValueError, match="Unsupported quant level"):
        service.run("fake-model", "Q9_WEIRD", "hello", 16)


def test_run_fails_gracefully_when_ollama_unreachable():
    service = QuantizationService(_gatekeeper(), "http://localhost:1")
    metrics = service.run("fake-model", "Q4_K_M", "hello", 16)
    assert metrics.succeeded is False
    assert metrics.error is not None
