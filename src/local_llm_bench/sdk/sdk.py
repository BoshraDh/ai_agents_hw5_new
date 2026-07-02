"""LocalLLMBenchSDK — the single entry point for all business logic.

The CLI (main.py) and the Jupyter notebook must only call methods on this class;
no business logic may live outside the SDK/services layers (guidelines section 4.1).
"""
from __future__ import annotations

from pathlib import Path

from local_llm_bench.services.airllm_service import AirllmService
from local_llm_bench.services.benchmark_service import BenchmarkService, ExperimentConfig
from local_llm_bench.services.cost_analysis_service import BreakevenResult, CostAnalysisService
from local_llm_bench.services.model_loader_service import ModelLoaderService
from local_llm_bench.services.model_roofline_service import ModelRooflineService
from local_llm_bench.services.quantization_service import QuantizationService
from local_llm_bench.services.report_service import ReportService
from local_llm_bench.shared.config import ConfigManager
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.hardware_probe import HardwareProbeMixin
from local_llm_bench.shared.metrics import RunMetrics


class LocalLLMBenchSDK(HardwareProbeMixin):
    """Single entry point exposing baseline/AirLLM/quantized runs, reporting, and economic analysis."""

    def __init__(self, project_root: Path | None = None):
        self._config = ConfigManager(project_root)
        settings = self._config.get_benchmark_settings()
        hf_gatekeeper = ApiGatekeeper(self._config.get_rate_limit("huggingface"))
        ollama_gatekeeper = ApiGatekeeper(self._config.get_rate_limit("ollama"))

        self._model_loader = ModelLoaderService(hf_gatekeeper, settings.assumed_tdp_watts)
        self._airllm = AirllmService(
            hf_gatekeeper, settings.airllm_layer_shards_saving_path, settings.assumed_tdp_watts,
        )
        self._quantization = QuantizationService(
            ollama_gatekeeper, self._config.get_ollama_host(), settings.assumed_tdp_watts,
        )
        self._benchmark = BenchmarkService(self._model_loader, self._airllm, self._quantization)
        self._report = ReportService(Path(settings.assets_dir))
        self._roofline = ModelRooflineService(Path(settings.assets_dir))
        self._cost_analysis = CostAnalysisService(self._config.get_economic_assumptions())

    def run_baseline(self, prompt: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        return self._model_loader.run(settings.model_name, settings.precision, prompt, max_new_tokens)

    def run_airllm(self, prompt: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        return self._airllm.run(settings.model_name, settings.precision, prompt, max_new_tokens)

    def run_quantized(self, prompt: str, quant_level: str, max_new_tokens: int) -> RunMetrics:
        settings = self._config.get_benchmark_settings()
        tag = settings.quant_ollama_tags.get(quant_level, settings.ollama_tag)
        return self._quantization.run(tag, quant_level, prompt, max_new_tokens)

    def run_full_benchmark_suite(self) -> Path:
        settings = self._config.get_benchmark_settings()
        experiment = ExperimentConfig(settings=settings)
        return self._benchmark.run_full_suite(experiment)

    def generate_report(self, results_path: Path) -> Path:
        return self._report.generate(results_path)

    def run_economic_analysis(self, avg_run_seconds_per_request: float) -> BreakevenResult:
        settings = self._config.get_benchmark_settings()
        result = self._cost_analysis.find_breakeven(settings.assumed_tdp_watts, avg_run_seconds_per_request)
        self._report.plot_breakeven(result)
        return result

    def generate_model_roofline(self, results_path: Path, model_params_billion: float) -> Path:
        df = self._report.load_results(results_path)
        roofline_assumptions = self._config.get_roofline_assumptions()
        return self._roofline.plot_model_roofline(df, model_params_billion, roofline_assumptions)
