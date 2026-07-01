"""Reads saved results/*.json and produces comparison tables and charts under assets/.

Reporting is intentionally decoupled from experiment execution: re-styling a chart
never requires re-running any model.
"""
from __future__ import annotations

import json
from pathlib import Path

from local_llm_bench.services.cost_analysis_service import BreakevenResult

_BYTES_PER_PARAM_BY_PRECISION = {"fp32": 4.0, "fp16": 2.0, "bf16": 2.0, "Q4_K_M": 0.5, "Q2_K": 0.25}


class ReportService:
    """Builds a comparison table plus bar/line charts from persisted RunMetrics JSON files."""

    def __init__(self, assets_dir: Path):
        self._assets_dir = assets_dir

    def _load_results(self, results_path: Path):
        import pandas as pd

        if not results_path.exists() or not any(results_path.glob("*.json")):
            raise FileNotFoundError(f"No results found under {results_path}")
        records = []
        for file in sorted(results_path.glob("*.json")):
            with open(file, encoding="utf-8") as f:
                records.extend(json.load(f))
        return pd.DataFrame.from_records(records)

    def generate(self, results_path: Path) -> Path:
        df = self._load_results(results_path)
        self._assets_dir.mkdir(parents=True, exist_ok=True)

        summary = (
            df[df["succeeded"]]
            .groupby("method")
            .agg(
                avg_peak_ram_mb=("peak_ram_mb", "mean"),
                avg_tokens_per_sec=("tokens_per_sec", "mean"),
                avg_load_time_sec=("load_time_sec", "mean"),
            )
            .reset_index()
        )
        summary.to_csv(self._assets_dir / "summary_table.csv", index=False)

        self._plot_peak_ram_bar(summary)
        self._plot_tokens_per_sec_line(df)
        return self._assets_dir

    def _plot_peak_ram_bar(self, summary) -> None:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        ax.bar(summary["method"], summary["avg_peak_ram_mb"], color=["#4C72B0", "#55A868", "#C44E52"])
        ax.set_ylabel("Peak RAM (MB)")
        ax.set_title("Peak RAM usage by execution method")
        fig.tight_layout()
        fig.savefig(self._assets_dir / "peak_ram_comparison.png")
        plt.close(fig)

    def _plot_tokens_per_sec_line(self, df) -> None:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        for method, group in df[df["succeeded"]].groupby("method"):
            grouped = group.groupby("max_new_tokens")["tokens_per_sec"].mean()
            ax.plot(grouped.index, grouped.values, marker="o", label=method)
        ax.set_xlabel("Requested output length (tokens)")
        ax.set_ylabel("Tokens / sec")
        ax.set_title("Throughput vs. output length (sensitivity analysis)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(self._assets_dir / "tokens_per_sec_vs_length.png")
        plt.close(fig)

    def plot_breakeven(self, result: BreakevenResult) -> Path:
        """Original economic-analysis chart (ex05 section 5.5, mandatory) — cumulative
        monthly cost of On-Prem vs. API against usage volume, with the break-even point."""
        import matplotlib.pyplot as plt

        self._assets_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        ax.plot(result.usage_volumes, result.api_costs, marker="o", label="API (third-party)")
        ax.plot(result.usage_volumes, result.onprem_costs, marker="o", label="On-Prem")
        if result.breakeven_volume is not None:
            ax.axvline(result.breakeven_volume, color="gray", linestyle="--",
                       label=f"Break-even ~{result.breakeven_volume} req/month")
        ax.set_xscale("log")
        ax.set_xlabel("Monthly usage volume (requests)")
        ax.set_ylabel("Monthly cost (USD)")
        ax.set_title("On-Prem vs. API cost break-even")
        ax.legend()
        fig.tight_layout()
        out_path = self._assets_dir / "breakeven_analysis.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path

    def plot_model_roofline(self, df, model_params_billion: float, roofline_assumptions: dict) -> Path:
        """Original extension (PLAN.md ADR-6): illustrates whether each method operates in a
        compute-bound or memory-bound regime. Ceiling values are ASSUMED (config-driven), not
        vendor-measured — documented explicitly in docs/PRD_benchmark_reporting.md."""
        import matplotlib.pyplot as plt
        import numpy as np

        peak_gflops = roofline_assumptions["assumed_peak_gflops"]
        bandwidth_gbps = roofline_assumptions["assumed_memory_bandwidth_gbps"]

        self._assets_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
        intensities = np.logspace(-2, 3, 200)
        ax.plot(intensities, np.minimum(bandwidth_gbps * intensities, peak_gflops),
                color="black", linestyle="--", label="Roofline ceiling (assumed)")

        for _, row in df[df["succeeded"]].iterrows():
            bytes_per_param = _BYTES_PER_PARAM_BY_PRECISION.get(row["precision_or_quant"], 4.0)
            intensity = 2.0 / bytes_per_param
            achieved_gflops = row["tokens_per_sec"] * 2 * model_params_billion
            ax.scatter(intensity, achieved_gflops, label=f"{row['method']} ({row['precision_or_quant']})")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Arithmetic Intensity (FLOPs/byte, by precision)")
        ax.set_ylabel("Achieved GFLOP/s")
        ax.set_title("Model Roofline (illustrative, assumption-based)")
        ax.legend(fontsize=7)
        fig.tight_layout()
        out_path = self._assets_dir / "model_roofline.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path
