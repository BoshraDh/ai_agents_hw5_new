"""AirLLM execution: layer-by-layer CPU inference via mmap, trading latency for RAM.

Same model, same prompts as ModelLoaderService, so the two RunMetrics are directly
comparable — this is the core contrast the assignment asks to analyze in depth.
"""
from __future__ import annotations

import time

from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics


class AirllmService(BaseMetricsCollectorMixin):
    """Runs the same model as ModelLoaderService but through AirLLM's layer-by-layer loader."""

    def __init__(self, gatekeeper: ApiGatekeeper):
        self._gatekeeper = gatekeeper

    def run(self, model_name: str, precision: str, prompt: str, max_new_tokens: int) -> RunMetrics:
        from airllm import AutoModel

        self._start_ram_sampling()
        wall_start = time.monotonic()
        try:
            load_start = time.monotonic()
            model = self._gatekeeper.execute(
                lambda: AutoModel.from_pretrained(model_name),
                description=f"AirLLM load {model_name}",
            )
            load_time = time.monotonic() - load_start

            input_ids = model.tokenizer(prompt, return_tensors="pt")
            gen_start = time.monotonic()
            output_ids = model.generate(
                input_ids["input_ids"], max_new_tokens=max_new_tokens, use_cache=True,
            )
            generation_time = time.monotonic() - gen_start

            generated_text = model.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            new_tokens = output_ids.shape[1] - input_ids["input_ids"].shape[1]
            tokens_per_sec = new_tokens / generation_time if generation_time > 0 else 0.0

            return RunMetrics(
                method="airllm",
                model_name=model_name,
                precision_or_quant=precision,
                prompt_tokens=input_ids["input_ids"].shape[1],
                max_new_tokens=max_new_tokens,
                load_time_sec=round(load_time, 3),
                time_to_first_token_sec=round(generation_time / max(new_tokens, 1), 3),
                tokens_per_sec=round(tokens_per_sec, 3),
                peak_ram_mb=round(self._stop_ram_sampling(), 1),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
                generated_text=generated_text,
            )
        except Exception as exc:  # noqa: BLE001
            self._stop_ram_sampling()
            return RunMetrics(
                method="airllm", model_name=model_name, precision_or_quant=precision,
                prompt_tokens=0, max_new_tokens=max_new_tokens, succeeded=False, error=str(exc),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
            )
