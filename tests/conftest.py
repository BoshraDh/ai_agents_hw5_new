"""Shared pytest fixtures: config fixtures, and fake torch/transformers/airllm modules
so services can be unit-tested without the heavy real ML dependencies being installed
or any network access (guidelines section 6.1: tests never depend on external services).
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False,
                      help="run slow/real integration tests that hit real services")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: real model downloads/execution, skipped by default")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def sample_setup_config() -> dict:
    return {
        "version": "1.00",
        "benchmark": {
            "model_name": "microsoft/Phi-3-medium-4k-instruct",
            "fallback_model_name": "microsoft/Phi-3-mini-4k-instruct",
            "precision": "fp32",
            "max_new_tokens_options": [16, 64],
            "prompts": ["Explain virtual memory in one paragraph."],
            "quant_levels": ["Q4_K_M", "Q2_K"],
            "results_dir": "results",
            "assets_dir": "assets",
        },
        "ollama": {"host": "http://localhost:11434"},
    }


@pytest.fixture
def sample_rate_limits_config() -> dict:
    default = {"requests_per_minute": 30, "requests_per_hour": 500, "concurrent_max": 5,
               "retry_after_seconds": 0, "max_retries": 2}
    return {
        "rate_limits": {
            "version": "1.00",
            "services": {
                "default": default,
                "huggingface": {**default, "requests_per_minute": 10},
                "ollama": {**default, "requests_per_minute": 20},
            },
        }
    }


@pytest.fixture
def project_root(tmp_path: Path, sample_setup_config: dict, sample_rate_limits_config: dict) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "setup.json").write_text(json.dumps(sample_setup_config), encoding="utf-8")
    (config_dir / "rate_limits.json").write_text(json.dumps(sample_rate_limits_config), encoding="utf-8")
    return tmp_path


class FakeTensor:
    """Minimal stand-in for a torch tensor: only what the services actually touch."""

    def __init__(self, shape: tuple[int, int]):
        self.shape = shape

    def __getitem__(self, _idx):
        return self


@pytest.fixture
def fake_ml_stack(monkeypatch):
    """Injects fake torch/transformers/airllm modules into sys.modules."""
    fake_torch = types.ModuleType("torch")
    fake_torch.float32 = "float32"
    fake_torch.float16 = "float16"
    fake_torch.bfloat16 = "bfloat16"
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    tokenizer = MagicMock()
    tokenizer.return_value = {"input_ids": FakeTensor((1, 5))}
    tokenizer.decode.return_value = "generated text"

    model = MagicMock()
    model.generate.return_value = FakeTensor((1, 25))

    fake_transformers = types.ModuleType("transformers")
    fake_transformers.AutoTokenizer = MagicMock(from_pretrained=MagicMock(return_value=tokenizer))
    fake_transformers.AutoModelForCausalLM = MagicMock(from_pretrained=MagicMock(return_value=model))
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    airllm_model = MagicMock()
    airllm_model.tokenizer = tokenizer
    airllm_model.generate.return_value = FakeTensor((1, 25))
    fake_airllm = types.ModuleType("airllm")
    fake_airllm.AutoModel = MagicMock(from_pretrained=MagicMock(return_value=airllm_model))
    monkeypatch.setitem(sys.modules, "airllm", fake_airllm)

    return {"tokenizer": tokenizer, "model": model, "airllm_model": airllm_model}
