"""Orchestrates the full experiment matrix (method x prompt x output length) and persists results.

Depends only on the shared run(...) interface of the three execution services, so a
fourth method could be added later without touching this file (see PLAN.md ADR-2).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from local_llm_bench.services.airllm_service import AirllmService
from local_llm_bench.services.model_loader_service import ModelLoaderService
from local_llm_bench.services.quantization_service import QuantizationService
from local_llm_bench.shared.config import BenchmarkSettings
from local_llm_bench.shared.metrics import RunMetrics


@dataclass
class ExperimentConfig:
    settings: BenchmarkSettings


class BenchmarkService:
    """Runs baseline, AirLLM, and quantized services across the configured prompt/length matrix."""

    def __init__(
        self,
        model_loader: ModelLoaderService,
        airllm: AirllmService,
        quantization: QuantizationService,
    ):
        self._model_loader = model_loader
        self._airllm = airllm
        self._quantization = quantization

    def run_full_suite(self, experiment: ExperimentConfig) -> Path:
        settings = experiment.settings
        results: list[RunMetrics] = []

        for prompt in settings.prompts:
            for max_tokens in settings.max_new_tokens_options:
                results.append(
                    self._model_loader.run(settings.model_name, settings.precision, prompt, max_tokens)
                )
                results.append(
                    self._airllm.run(settings.model_name, settings.precision, prompt, max_tokens)
                )
                for quant_level in settings.quant_levels:
                    tag = settings.quant_ollama_tags.get(quant_level, settings.ollama_tag)
                    results.append(
                        self._quantization.run(tag, quant_level, prompt, max_tokens)
                    )

        return self._save_results(results, Path(settings.results_dir))

    @staticmethod
    def _save_results(results: list[RunMetrics], results_dir: Path) -> Path:
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = results_dir / f"run_{timestamp}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)
        return out_path
