"""Unit tests for QuantizationService (Ollama/GGUF execution path)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

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


@patch("subprocess.run")
@patch("requests.post")
@patch("requests.get")
def test_run_parses_ttft_tpot_from_ollama_native_fields(mock_get, mock_post, mock_subprocess_run):
    mock_get.return_value = MagicMock(raise_for_status=MagicMock())
    mock_post.return_value = MagicMock(json=MagicMock(return_value={
        "response": "generated text", "eval_count": 21, "prompt_eval_count": 5,
        "prompt_eval_duration": 500_000_000,  # 0.5s
        "eval_duration": 2_000_000_000,  # 2.0s over 21 tokens
    }))

    service = QuantizationService(_gatekeeper(), "http://localhost:11434", assumed_tdp_watts=28.0)
    metrics = service.run("fake-model", "Q4_K_M", "hello", 16)

    assert metrics.succeeded is True
    assert metrics.ttft_sec == pytest.approx(0.5, abs=1e-6)
    assert metrics.tpot_sec == pytest.approx(2.0 / 20, abs=1e-6)
    assert metrics.estimated_power_wh >= 0
