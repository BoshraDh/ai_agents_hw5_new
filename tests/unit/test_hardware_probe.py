"""Unit tests for HardwareProbeMixin."""
from __future__ import annotations

from unittest.mock import patch

from local_llm_bench.shared.hardware_probe import HardwareProbeMixin, HardwareSpec


class _Probe(HardwareProbeMixin):
    pass


def test_probe_hardware_returns_hardware_spec():
    spec = _Probe().probe_hardware()
    assert isinstance(spec, HardwareSpec)
    assert spec.total_ram_gb > 0
    assert spec.logical_cores > 0


@patch("subprocess.run")
def test_detect_gpu_no_cuda_falls_back_gracefully(mock_run):
    mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
    name, has_cuda = HardwareProbeMixin._detect_gpu()
    assert has_cuda is False
    assert "No dedicated CUDA GPU" in name


def test_warn_if_model_too_large_triggers_warning():
    spec = HardwareSpec(cpu_name="test", physical_cores=4, logical_cores=8,
                         total_ram_gb=16.0, gpu_name="none", has_cuda_gpu=False)
    warning = _Probe().warn_if_model_too_large(model_params_billion=70, bytes_per_param=4, spec=spec)
    assert warning is not None
    assert "may exceed" in warning


def test_warn_if_model_too_large_returns_none_when_fits():
    spec = HardwareSpec(cpu_name="test", physical_cores=4, logical_cores=8,
                         total_ram_gb=76.0, gpu_name="none", has_cuda_gpu=False)
    warning = _Probe().warn_if_model_too_large(model_params_billion=3.8, bytes_per_param=2, spec=spec)
    assert warning is None
