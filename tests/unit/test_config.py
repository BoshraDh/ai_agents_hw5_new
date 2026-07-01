"""Unit tests for ConfigManager."""
from __future__ import annotations

from local_llm_bench.shared.config import ConfigManager


def test_get_benchmark_settings_reads_model_name(project_root):
    config = ConfigManager(project_root)
    settings = config.get_benchmark_settings()
    assert settings.model_name == "microsoft/Phi-3-medium-4k-instruct"
    assert settings.precision == "fp32"


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
