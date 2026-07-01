"""Unit tests for LocalLLMBenchSDK — verifies wiring: config values reach the services."""
from __future__ import annotations

from local_llm_bench.sdk import LocalLLMBenchSDK


def test_run_baseline_uses_configured_model(project_root, fake_ml_stack):
    sdk = LocalLLMBenchSDK(project_root)
    metrics = sdk.run_baseline("hello", 16)
    assert metrics.model_name == "microsoft/Phi-3-medium-4k-instruct"
    assert metrics.succeeded is True


def test_run_airllm_uses_configured_model(project_root, fake_ml_stack):
    sdk = LocalLLMBenchSDK(project_root)
    metrics = sdk.run_airllm("hello", 16)
    assert metrics.method == "airllm"
    assert metrics.succeeded is True


def test_probe_hardware_returns_spec(project_root, fake_ml_stack):
    sdk = LocalLLMBenchSDK(project_root)
    spec = sdk.probe_hardware()
    assert spec.total_ram_gb > 0
