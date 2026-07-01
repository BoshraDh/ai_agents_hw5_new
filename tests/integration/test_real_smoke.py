"""Real end-to-end smoke test against actual Hugging Face / AirLLM / Ollama.

Skipped by default (heavy downloads, long runtime on CPU-only hardware). Run explicitly
with real dependencies installed and internet access:

    uv run pytest tests/integration/test_real_smoke.py --run-slow

Not executed as part of this project phase (see docs/TODO.md Phase 4).
"""
from __future__ import annotations

import pytest

from local_llm_bench.sdk import LocalLLMBenchSDK


@pytest.mark.slow
def test_real_baseline_smoke():
    sdk = LocalLLMBenchSDK()
    metrics = sdk.run_baseline("Say hello in one word.", max_new_tokens=8)
    assert metrics.succeeded is True
    assert metrics.tokens_per_sec >= 0


@pytest.mark.slow
def test_real_airllm_smoke():
    sdk = LocalLLMBenchSDK()
    metrics = sdk.run_airllm("Say hello in one word.", max_new_tokens=8)
    assert metrics.succeeded is True
    assert metrics.peak_ram_mb > 0
