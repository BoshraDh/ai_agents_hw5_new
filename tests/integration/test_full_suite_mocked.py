"""Integration test: full benchmark suite end-to-end with all external calls mocked/faked."""
from __future__ import annotations

import json

from local_llm_bench.sdk import LocalLLMBenchSDK
from local_llm_bench.services.quantization_service import QuantizationService
from local_llm_bench.shared.metrics import RunMetrics


def test_full_benchmark_suite_end_to_end(project_root, fake_ml_stack, monkeypatch):
    def fake_quant_run(self, ollama_model_tag, quant_level, prompt, max_new_tokens):
        return RunMetrics(method="quantized", model_name=ollama_model_tag,
                           precision_or_quant=quant_level, prompt_tokens=5,
                           max_new_tokens=max_new_tokens)

    monkeypatch.setattr(QuantizationService, "run", fake_quant_run)

    sdk = LocalLLMBenchSDK(project_root)
    out_path = sdk.run_full_benchmark_suite()

    assert out_path.exists()
    records = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(records) > 0
    assert {r["method"] for r in records} == {"baseline", "airllm", "quantized"}
    assert all(r["succeeded"] for r in records)
