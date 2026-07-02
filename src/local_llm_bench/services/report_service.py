"""Reads saved results/*.json and produces comparison tables and charts under assets/.

Reporting is intentionally decoupled from experiment execution: re-styling a chart
never requires re-running any model.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

# This service only ever saves charts to disk; force the non-interactive Agg backend
# so it works headless/in CI and doesn't depend on a working Tk install (this Windows
# uv-managed Python was missing tk.tcl, which crashed the default TkAgg backend).
matplotlib.use("Agg")

from local_llm_bench.services.cost_analysis_service import BreakevenResult


class ReportService:
    """Builds a comparison table plus bar/line charts from persisted RunMetrics JSON files."""

    def __init__(self, assets_dir: Path):
        self._assets_dir = assets_dir

    def load_results(self, results_path: Path):
        """Public loader — reused by generate() and by SDK.generate_model_roofline().

        Accepts both the list-of-RunMetrics format written by BenchmarkService and the
        single-object evidence files saved by hand during Phase 4 (e.g.
        results/airllm_phi3_medium_success.json), which carry one RunMetrics-shaped dict
        plus extra descriptive fields (purpose, root_cause, ...). results_path may also
        contain non-experiment artifacts (e.g. economic_analysis.json, which has its own
        unrelated schema) -- these are skipped rather than corrupting the comparison table,
        since they lack the "method"/"succeeded" fields every RunMetrics record has.
        """
        import pandas as pd

        if not results_path.exists() or not any(results_path.glob("*.json")):
            raise FileNotFoundError(f"No results found under {results_path}")
        records = []
        for file in sorted(results_path.glob("*.json")):
            with open(file, encoding="utf-8") as f:
                parsed = json.load(f)
            for record in parsed if isinstance(parsed, list) else [parsed]:
                if "method" in record and "succeeded" in record:
                    records.append(record)
        if not records:
            raise FileNotFoundError(f"No RunMetrics-shaped result records found under {results_path}")
        return pd.DataFrame.from_records(records)

    def generate(self, results_path: Path) -> Path:
        df = self.load_results(results_path)
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
