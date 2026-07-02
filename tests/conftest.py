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
        "version": "1.01",
        "benchmark": {
            "model_name": "microsoft/Phi-3-medium-4k-instruct",
            "fallback_model_name": "microsoft/Phi-3-mini-4k-instruct",
            "precision": "fp32",
            "max_new_tokens_options": [16, 64],
            "prompts": ["Explain virtual memory in one paragraph."],
            "quant_levels": ["Q4_0", "Q2_K"],
            "results_dir": "results",
            "assets_dir": "assets",
            "assumed_tdp_watts": 28.0,
            "ollama_tag": "phi3:medium",
        },
        "airllm": {"layer_shards_saving_path": "data/airllm_cache"},
        "roofline": {"assumed_peak_gflops": 200.0, "assumed_memory_bandwidth_gbps": 50.0},
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
def sample_economic_assumptions() -> dict:
    return {
        "version": "1.00",
        "api_pricing": {
            "provider": "test-provider",
            "price_per_1k_input_tokens_usd": 0.03,
            "price_per_1k_output_tokens_usd": 0.06,
            "cached_token_discount_ratio": 0.5,
        },
        "on_prem": {
            "hardware_cost_usd": 1500.0,
            "hardware_lifespan_years": 3,
            "electricity_price_usd_per_kwh": 0.18,
            "annual_maintenance_usd": 50.0,
        },
        "cloud_gpu": {"include": False, "price_per_gpu_hour_usd": 2.5},
        "usage_scenario": {
            "avg_input_tokens_per_request": 500,
            "avg_output_tokens_per_request": 200,
            "usage_volumes_per_month": [10, 100, 1000, 10000, 100000],
        },
    }


@pytest.fixture
def project_root(
    tmp_path: Path, sample_setup_config: dict, sample_rate_limits_config: dict,
    sample_economic_assumptions: dict, monkeypatch,
) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "setup.json").write_text(json.dumps(sample_setup_config), encoding="utf-8")
    (config_dir / "rate_limits.json").write_text(json.dumps(sample_rate_limits_config), encoding="utf-8")
    (config_dir / "economic_assumptions.json").write_text(
        json.dumps(sample_economic_assumptions), encoding="utf-8",
    )
    # results_dir/assets_dir in setup.json are relative paths, resolved against the
    # process cwd by BenchmarkService/ReportService -- without this chdir, tests using
    # this fixture would silently write their fake results into the real project's
    # results/ directory instead of the sandbox (this exact bug happened and polluted
    # results/ with run_*.json files from test_full_suite_mocked.py).
    monkeypatch.chdir(tmp_path)
    return tmp_path


class FakeTensor:
    """Minimal stand-in for a torch tensor: only what the services actually touch."""

    def __init__(self, shape: tuple[int, int]):
        self.shape = shape

    def __getitem__(self, _idx):
        return self


class FakeStreamer:
    """Stand-in for transformers.TextIteratorStreamer: a pre-populated iterable of text
    chunks, so tests don't need real threading/streamer synchronization with generate()."""

    def __init__(self, chunks: list[str]):
        self._chunks = chunks

    def __iter__(self):
        yield from self._chunks


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
    fake_transformers.TextIteratorStreamer = MagicMock(
        return_value=FakeStreamer(["gen", "erated", " text"]),
    )
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    airllm_model = MagicMock()
    airllm_model.tokenizer = tokenizer
    airllm_model.generate.return_value = FakeTensor((1, 25))
    fake_airllm = types.ModuleType("airllm")
    fake_airllm.AutoModel = MagicMock(from_pretrained=MagicMock(return_value=airllm_model))
    monkeypatch.setitem(sys.modules, "airllm", fake_airllm)

    return {"tokenizer": tokenizer, "model": model, "airllm_model": airllm_model}
