"""Centralized configuration loading.

The only module allowed to read config/*.json or environment variables directly
(guidelines section 7.3: single configuration architecture, no hardcoded values).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from local_llm_bench.constants import DEFAULT_CONFIG_PATH, DEFAULT_RATE_LIMIT_PATH


@dataclass
class BenchmarkSettings:
    model_name: str
    fallback_model_name: str
    precision: str
    max_new_tokens_options: list[int]
    prompts: list[str]
    quant_levels: list[str]
    results_dir: str
    assets_dir: str


class ConfigManager:
    """Loads config/setup.json + config/rate_limits.json + .env, exposes typed access."""

    def __init__(self, project_root: Path | None = None):
        self._root = project_root or Path.cwd()
        self._load_env()
        self._setup = self._load_json(self._root / DEFAULT_CONFIG_PATH)
        self._rate_limits = self._load_json(self._root / DEFAULT_RATE_LIMIT_PATH)

    def _load_env(self) -> None:
        from dotenv import load_dotenv

        load_dotenv(self._root / ".env")

    @staticmethod
    def _load_json(path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_benchmark_settings(self) -> BenchmarkSettings:
        b = self._setup["benchmark"]
        return BenchmarkSettings(
            model_name=b["model_name"],
            fallback_model_name=b["fallback_model_name"],
            precision=b["precision"],
            max_new_tokens_options=b["max_new_tokens_options"],
            prompts=b["prompts"],
            quant_levels=b["quant_levels"],
            results_dir=b["results_dir"],
            assets_dir=b["assets_dir"],
        )

    def get_rate_limit(self, service: str) -> dict:
        services = self._rate_limits["rate_limits"]["services"]
        return services.get(service, services["default"])

    def get_hf_token(self) -> str | None:
        return os.environ.get("HF_TOKEN")

    def get_ollama_host(self) -> str:
        return self._setup.get("ollama", {}).get("host", "http://localhost:11434")
