"""Reads saved results/*.json and produces comparison tables and charts under assets/.

Reporting is intentionally decoupled from experiment execution: re-styling a chart
never requires re-running any model.
"""
from __future__ import annotations

import json
from pathlib import Path


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
