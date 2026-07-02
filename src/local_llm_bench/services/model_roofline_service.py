"""Builds the Model Roofline chart -- the project's chosen original extension
(ex05 section 5.7, docs/PLAN.md ADR-6).

Split out of ReportService (which reads results/*.json and builds the baseline
comparison charts) to keep each file under the 150-line guideline limit and to
give the original-extension logic a single, separately testable home.
"""
from __future__ import annotations

from pathlib import Path

_BYTES_PER_PARAM_BY_PRECISION = {"fp32": 4.0, "fp16": 2.0, "bf16": 2.0, "Q4_K_M": 0.5, "Q2_K": 0.25}


class ModelRooflineService:
    """Illustrates whether each execution method is compute-bound or memory-bound.

    Ceiling values are ASSUMED (config-driven), not vendor-measured -- documented
    explicitly in docs/PRD_benchmark_reporting.md.
    """

    def __init__(self, assets_dir: Path):
        self._assets_dir = assets_dir

    def _build_roofline_figure(self, df, model_params_billion: float, roofline_assumptions: dict):
        """Builds the figure/axes without saving -- split out so tests can inspect
        legend content directly instead of parsing a saved PNG."""
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd

        peak_gflops = roofline_assumptions["assumed_peak_gflops"]
        bandwidth_gbps = roofline_assumptions["assumed_memory_bandwidth_gbps"]

        fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
        intensities = np.logspace(-2, 3, 200)
        ax.plot(intensities, np.minimum(bandwidth_gbps * intensities, peak_gflops),
                color="black", linestyle="--", label="Roofline ceiling (assumed)")

        for _, row in df[df["succeeded"]].iterrows():
            # Some hand-saved Phase 4 evidence files predate the precision_or_quant field
            # (or use "quantization_level" instead) -- fall back rather than KeyError, and
            # be honest in the legend about which value (if any) was actually available.
            # (NaN is truthy in Python, so `x or y` would return a NaN instead of falling
            # through to y -- must check for real missing values with pd.isna explicitly.)
            precision_label = row.get("precision_or_quant")
            if pd.isna(precision_label):
                precision_label = row.get("quantization_level")
            if not isinstance(precision_label, str) or not precision_label:
                precision_label = "unknown"
            bytes_per_param = _BYTES_PER_PARAM_BY_PRECISION.get(precision_label, 4.0)
            intensity = 2.0 / bytes_per_param
            achieved_gflops = row["tokens_per_sec"] * 2 * model_params_billion
            ax.scatter(intensity, achieved_gflops, label=f"{row['method']} ({precision_label})")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Arithmetic Intensity (FLOPs/byte, by precision)")
        ax.set_ylabel("Achieved GFLOP/s")
        ax.set_title("Model Roofline (illustrative, assumption-based)")
        ax.legend(fontsize=7)
        fig.tight_layout()
        return fig, ax

    def plot_model_roofline(self, df, model_params_billion: float, roofline_assumptions: dict) -> Path:
        import matplotlib.pyplot as plt

        self._assets_dir.mkdir(parents=True, exist_ok=True)
        fig, _ax = self._build_roofline_figure(df, model_params_billion, roofline_assumptions)
        out_path = self._assets_dir / "model_roofline.png"
        fig.savefig(out_path)
        plt.close(fig)
        return out_path
