"""Runtime hardware detection (CPU/RAM/GPU) — feeds the report and pre-run sanity checks."""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass

from local_llm_bench.constants import BYTES_PER_GB


@dataclass
class HardwareSpec:
    cpu_name: str
    physical_cores: int
    logical_cores: int
    total_ram_gb: float
    gpu_name: str
    has_cuda_gpu: bool


class HardwareProbeMixin:
    """Mixin providing probe_hardware() — reused by the SDK and by services that need a
    pre-run sanity check (e.g. warn if the chosen model is too large for available RAM).
    """

    def probe_hardware(self) -> HardwareSpec:
        import psutil

        total_ram_gb = psutil.virtual_memory().total / BYTES_PER_GB
        gpu_name, has_cuda = self._detect_gpu()
        return HardwareSpec(
            cpu_name=platform.processor() or "unknown",
            physical_cores=psutil.cpu_count(logical=False) or 0,
            logical_cores=psutil.cpu_count(logical=True) or 0,
            total_ram_gb=round(total_ram_gb, 1),
            gpu_name=gpu_name,
            has_cuda_gpu=has_cuda,
        )

    @staticmethod
    def _detect_gpu() -> tuple[str, bool]:
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5, check=True,
            )
            name = out.stdout.strip().splitlines()[0]
            return name, True
        except Exception:  # noqa: BLE001 - nvidia-smi absence is expected on non-CUDA machines
            return "No dedicated CUDA GPU detected", False

    def warn_if_model_too_large(
        self, model_params_billion: float, bytes_per_param: float, spec: HardwareSpec
    ) -> str | None:
        estimated_gb = (model_params_billion * 1e9 * bytes_per_param) / BYTES_PER_GB
        if estimated_gb > spec.total_ram_gb * 0.9:
            return (
                f"Model estimated {estimated_gb:.1f}GB may exceed 90% of the "
                f"{spec.total_ram_gb:.1f}GB available RAM."
            )
        return None
