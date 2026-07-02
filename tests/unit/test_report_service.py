"""Unit tests for ReportService (reads persisted results, produces table + charts)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from local_llm_bench.services.cost_analysis_service import BreakevenResult
from local_llm_bench.services.report_service import ReportService

_RECORD_TEMPLATE = {
    "model_name": "m", "precision_or_quant": "fp32", "prompt_tokens": 5, "max_new_tokens": 16,
    "succeeded": True, "error": None, "load_time_sec": 1.0, "ttft_sec": 0.1, "tpot_sec": 0.05,
    "peak_ram_mb": 50000.0, "total_wall_time_sec": 10.0, "estimated_power_wh": 0.05,
    "generated_text": "x", "quality_note": None, "timestamp": "now",
}


def _write_results(results_dir: Path, records: list[dict]) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "run_test.json").write_text(json.dumps(records), encoding="utf-8")


def test_generate_raises_when_no_results(tmp_path: Path):
    service = ReportService(tmp_path / "assets")
    with pytest.raises(FileNotFoundError):
        service.generate(tmp_path / "results")


def test_generate_produces_summary_and_charts(tmp_path: Path):
    records = [
        {**_RECORD_TEMPLATE, "method": "baseline", "tokens_per_sec": 2.0, "peak_ram_mb": 50000.0},
        {**_RECORD_TEMPLATE, "method": "airllm", "tokens_per_sec": 0.5, "peak_ram_mb": 1500.0},
    ]
    results_dir = tmp_path / "results"
    _write_results(results_dir, records)

    service = ReportService(tmp_path / "assets")
    assets_path = service.generate(results_dir)

    assert (assets_path / "summary_table.csv").exists()
    assert (assets_path / "peak_ram_comparison.png").exists()
    assert (assets_path / "tokens_per_sec_vs_length.png").exists()


def test_load_results_accepts_single_object_files_and_skips_non_experiment_artifacts(tmp_path: Path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    # list-of-records file, written by BenchmarkService
    (results_dir / "run_test.json").write_text(
        json.dumps([{**_RECORD_TEMPLATE, "method": "baseline", "tokens_per_sec": 2.0}]),
        encoding="utf-8",
    )
    # single-object evidence file, saved by hand (as in results/airllm_*_success.json)
    (results_dir / "airllm_evidence.json").write_text(
        json.dumps({**_RECORD_TEMPLATE, "method": "airllm", "tokens_per_sec": 0.5, "purpose": "demo"}),
        encoding="utf-8",
    )
    # non-experiment artifact (as in results/economic_analysis.json) -- no "method"/"succeeded"
    (results_dir / "economic_analysis.json").write_text(
        json.dumps({"breakeven_volume_requests_per_month": 10000}), encoding="utf-8",
    )

    service = ReportService(tmp_path / "assets")
    df = service.load_results(results_dir)

    assert len(df) == 2
    assert set(df["method"]) == {"baseline", "airllm"}


def test_plot_breakeven_saves_chart(tmp_path: Path):
    service = ReportService(tmp_path / "assets")
    result = BreakevenResult(
        usage_volumes=[10, 100, 1000], api_costs=[1.0, 10.0, 100.0],
        onprem_costs=[50.0, 55.0, 90.0], breakeven_volume=1000, assumptions={},
    )
    out_path = service.plot_breakeven(result)
    assert out_path.exists()
    assert out_path.name == "breakeven_analysis.png"


