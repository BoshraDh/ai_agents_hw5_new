"""Unit tests for BenchmarkService orchestration (uses fake service doubles, no real ML libs)."""
from __future__ import annotations

import json
from pathlib import Path

from local_llm_bench.services.benchmark_service import BenchmarkService, ExperimentConfig
from local_llm_bench.shared.config import BenchmarkSettings
from local_llm_bench.shared.metrics import RunMetrics


class _FakeService:
    """Stands in for ModelLoaderService/AirllmService/QuantizationService in orchestration tests."""

    def __init__(self, method_name: str):
        self.method_name = method_name
        self.call_count = 0

    def run(self, *args, **_kwargs) -> RunMetrics:
        self.call_count += 1
        return RunMetrics(method=self.method_name, model_name="fake-model", precision_or_quant="fp32",
                           prompt_tokens=5, max_new_tokens=args[-1] if args else 10)


def test_run_full_suite_saves_expected_number_of_records(tmp_path: Path):
    settings = BenchmarkSettings(
        model_name="fake/model", fallback_model_name="fake/small", precision="fp32",
        max_new_tokens_options=[16, 32], prompts=["p1", "p2"], quant_levels=["Q4_K_M"],
        results_dir=str(tmp_path / "results"), assets_dir=str(tmp_path / "assets"),
    )
    baseline, airllm, quantized = _FakeService("baseline"), _FakeService("airllm"), _FakeService("quantized")
    service = BenchmarkService(baseline, airllm, quantized)

    out_path = service.run_full_suite(ExperimentConfig(settings=settings, ollama_model_tag="fake-model"))

    assert out_path.exists()
    records = json.loads(out_path.read_text(encoding="utf-8"))
    # 2 prompts x 2 lengths x (1 baseline + 1 airllm + 1 quant level) = 12
    assert len(records) == 12
    assert baseline.call_count == 4
    assert airllm.call_count == 4
    assert quantized.call_count == 4
