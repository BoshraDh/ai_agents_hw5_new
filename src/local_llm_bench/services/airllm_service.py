"""AirLLM execution: layer-by-layer CPU inference via mmap, trading latency for RAM.

Same model, same prompts as ModelLoaderService, so the two RunMetrics are directly
comparable — this is the core contrast the assignment asks to analyze in depth.
"""
from __future__ import annotations

import time

from local_llm_bench.constants import DEFAULT_ASSUMED_TDP_WATTS, SECONDS_PER_HOUR
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.generation_timing import StreamingTimingMixin
from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics


class AirllmService(BaseMetricsCollectorMixin, StreamingTimingMixin):
    """Runs the same model as ModelLoaderService but through AirLLM's layer-by-layer loader."""

    def __init__(
        self,
        gatekeeper: ApiGatekeeper,
        layer_shards_saving_path: str = "data/airllm_cache",
        assumed_tdp_watts: float = DEFAULT_ASSUMED_TDP_WATTS,
    ):
        self._gatekeeper = gatekeeper
        self._layer_shards_saving_path = layer_shards_saving_path
        self._assumed_tdp_watts = assumed_tdp_watts

    def run(self, model_name: str, precision: str, prompt: str, max_new_tokens: int) -> RunMetrics:
        from airllm import AutoModel
        from transformers import TextIteratorStreamer

        self._start_ram_sampling()
        wall_start = time.monotonic()
        try:
            load_start = time.monotonic()
            model = self._gatekeeper.execute(
                lambda: AutoModel.from_pretrained(
                    model_name, layer_shards_saving_path=self._layer_shards_saving_path,
                ),
                description=f"AirLLM load {model_name}",
            )
            load_time = time.monotonic() - load_start

            input_ids = model.tokenizer(prompt, return_tensors="pt")
            streamer = TextIteratorStreamer(model.tokenizer, skip_special_tokens=True, skip_prompt=True)
            generated_text, ttft, tpot, new_tokens = self._generate_with_timing(
                model.generate, streamer, {"input_ids": input_ids["input_ids"], "use_cache": True},
                max_new_tokens,
            )
            generation_time = ttft + tpot * max(new_tokens - 1, 0)
            tokens_per_sec = new_tokens / generation_time if generation_time > 0 else 0.0
            total_wall = time.monotonic() - wall_start

            return RunMetrics(
                method="airllm",
                model_name=model_name,
                precision_or_quant=precision,
                prompt_tokens=input_ids["input_ids"].shape[1],
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
        except Exception as exc:  # noqa: BLE001
            self._stop_ram_sampling()
            return RunMetrics(
                method="airllm", model_name=model_name, precision_or_quant=precision,
                prompt_tokens=0, max_new_tokens=max_new_tokens, succeeded=False, error=str(exc),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
            )
