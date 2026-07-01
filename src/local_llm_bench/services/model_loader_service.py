"""Baseline execution: full model load into RAM via transformers, then .generate() on CPU.

This is the "what happens when you try to run a large model on your own CPU" path
the assignment asks for — no GPU, no layer streaming, everything resident in RAM.
"""
from __future__ import annotations

import time

from local_llm_bench.constants import DEFAULT_ASSUMED_TDP_WATTS, SECONDS_PER_HOUR
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.generation_timing import StreamingTimingMixin
from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics


class ModelLoaderService(BaseMetricsCollectorMixin, StreamingTimingMixin):
    """Runs a Hugging Face model the standard way: load all weights, then generate."""

    def __init__(self, gatekeeper: ApiGatekeeper, assumed_tdp_watts: float = DEFAULT_ASSUMED_TDP_WATTS):
        self._gatekeeper = gatekeeper
        self._assumed_tdp_watts = assumed_tdp_watts

    def run(self, model_name: str, precision: str, prompt: str, max_new_tokens: int) -> RunMetrics:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

        dtype_map = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}
        if precision not in dtype_map:
            raise ValueError(f"Unsupported precision: {precision}")

        self._start_ram_sampling()
        wall_start = time.monotonic()
        try:
            tokenizer = self._gatekeeper.execute(
                lambda: AutoTokenizer.from_pretrained(model_name),
                description=f"download tokenizer {model_name}",
            )
            load_start = time.monotonic()
            model = self._gatekeeper.execute(
                lambda: AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype_map[precision]),
                description=f"download+load model {model_name}",
            )
            load_time = time.monotonic() - load_start

            inputs = tokenizer(prompt, return_tensors="pt")
            streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True, skip_prompt=True)
            generated_text, ttft, tpot, new_tokens = self._generate_with_timing(
                model.generate, streamer, dict(inputs), max_new_tokens,
            )
            generation_time = ttft + tpot * max(new_tokens - 1, 0)
            tokens_per_sec = new_tokens / generation_time if generation_time > 0 else 0.0
            total_wall = time.monotonic() - wall_start

            return RunMetrics(
                method="baseline",
                model_name=model_name,
                precision_or_quant=precision,
                prompt_tokens=inputs["input_ids"].shape[1],
                max_new_tokens=max_new_tokens,
                load_time_sec=round(load_time, 3),
                ttft_sec=round(ttft, 3),
                tpot_sec=round(tpot, 3),
                tokens_per_sec=round(tokens_per_sec, 3),
                peak_ram_mb=round(self._stop_ram_sampling(), 1),
                total_wall_time_sec=round(total_wall, 3),
                estimated_power_wh=round(self._assumed_tdp_watts * (total_wall / SECONDS_PER_HOUR), 4),
                generated_text=generated_text,
            )
        except Exception as exc:  # noqa: BLE001 - a failure here IS a valid experiment result
            self._stop_ram_sampling()
            return RunMetrics(
                method="baseline", model_name=model_name, precision_or_quant=precision,
                prompt_tokens=0, max_new_tokens=max_new_tokens, succeeded=False, error=str(exc),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
            )
