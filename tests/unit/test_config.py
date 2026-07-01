"""Unit tests for ConfigManager."""
from __future__ import annotations

from local_llm_bench.shared.config import ConfigManager


def test_get_benchmark_settings_reads_model_name(project_root):
    config = ConfigManager(project_root)
    settings = config.get_benchmark_settings()
    assert settings.model_name == "microsoft/Phi-3-medium-4k-instruct"
    assert settings.precision == "fp32"
    assert settings.assumed_tdp_watts == 28.0
    assert settings.airllm_layer_shards_saving_path == "data/airllm_cache"


def test_get_economic_assumptions_reads_pricing(project_root):
    config = ConfigManager(project_root)
    assumptions = config.get_economic_assumptions()
    assert assumptions["api_pricing"]["price_per_1k_input_tokens_usd"] == 0.03


def test_get_roofline_assumptions_reads_config(project_root):
    config = ConfigManager(project_root)
    roofline = config.get_roofline_assumptions()
    assert roofline["assumed_peak_gflops"] == 200.0


def test_get_rate_limit_falls_back_to_default(project_root):
    config = ConfigManager(project_root)
    limit = config.get_rate_limit("nonexistent_service")
    assert limit["requests_per_minute"] == 30


def test_get_rate_limit_returns_specific_service(project_root):
    config = ConfigManager(project_root)
    limit = config.get_rate_limit("huggingface")
    assert limit["requests_per_minute"] == 10


def test_get_hf_token_reads_env_var(project_root, monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "test-token-123")
    config = ConfigManager(project_root)
    assert config.get_hf_token() == "test-token-123"


def test_get_ollama_host_default(project_root):
    config = ConfigManager(project_root)
    assert config.get_ollama_host() == "http://localhost:11434"
