"""LocalLLMBenchSDK — the single entry point for all business logic.

The CLI (main.py) and the Jupyter notebook must only call methods on this class;
no business logic may live outside the SDK/services layers (guidelines section 4.1).
"""
from __future__ import annotations

from pathlib import Path

from local_llm_bench.services.airllm_service import AirllmService
from local_llm_bench.services.benchmark_service import BenchmarkService, ExperimentConfig
from local_llm_bench.services.model_loader_service import ModelLoaderService
from local_llm_bench.services.quantization_service import QuantizationService
from local_llm_bench.services.report_service import ReportService
from local_llm_bench.shared.config import ConfigManager
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.hardware_probe import HardwareProbeMixin
from local_llm_bench.shared.metrics import RunMetrics


class LocalLLMBenchSDK(HardwareProbeMixin):
    """Single entry point exposing baseline/AirLLM/quantized runs and reporting."""

    def __init__(self, project_root: Path | None = None):
        self._config = ConfigManager(project_root)
        hf_gatekeeper = ApiGatekeeper(self._config.get_rate_limit("huggingface"))
        ollama_gatekeeper = ApiGatekeeper(self._config.get_rate_limit("ollama"))

        self._model_loader = ModelLoaderService(hf_gatekeeper)
        self._airllm = AirllmService(hf_gatekeeper)
        self._quantization = QuantizationService(ollama_gatekeeper, self._config.get_ollama_host())
        self._benchmark = BenchmarkService(self._model_loader, self._airllm, self._quantization)
        self._report = ReportService(Path(self._config.get_benchmark_settings().assets_dir))

    def run_baseline(self, prompt: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        return self._model_loader.run(settings.model_name, settings.precision, prompt, max_new_tokens)

    def run_airllm(self, prompt: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        return self._airllm.run(settings.model_name, settings.precision, prompt, max_new_tokens)

    def run_quantized(self, prompt: str, quant_level: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        ollama_tag = settings.model_name.split("/")[-1].lower()
        return self._quantization.run(ollama_tag, quant_level, prompt, max_new_tokens)

    def run_full_benchmark_suite(self) -> Path:
        settings = self._config.get_benchmark_settings()
        ollama_tag = settings.model_name.split("/")[-1].lower()
        experiment = ExperimentConfig(settings=settings, ollama_model_tag=ollama_tag)
        return self._benchmark.run_full_suite(experiment)

    def generate_report(self, results_path: Path) -> Path:
        return self._report.generate(results_path)
