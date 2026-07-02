"""Quantized execution via a local Ollama daemon (GGUF weights, e.g. Q4_K_M / Q2_K)."""
from __future__ import annotations

import time

from local_llm_bench.constants import (
    DEFAULT_ASSUMED_TDP_WATTS,
    SECONDS_PER_HOUR,
    SUPPORTED_QUANT_LEVELS,
)
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics

_NANOSECONDS_PER_SECOND = 1_000_000_000


class QuantizationService(BaseMetricsCollectorMixin):
    """Runs a quantized GGUF variant of the model through the local Ollama HTTP API."""

    def __init__(
        self, gatekeeper: ApiGatekeeper, ollama_host: str,
        assumed_tdp_watts: float = DEFAULT_ASSUMED_TDP_WATTS,
    ):
        self._gatekeeper = gatekeeper
        self._host = ollama_host
        self._assumed_tdp_watts = assumed_tdp_watts

    def _ensure_available(self) -> None:
        import requests

        try:
            requests.get(f"{self._host}/api/tags", timeout=3).raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Ollama is not reachable at {self._host}. Run 'ollama serve' first."
            ) from exc

    def run(
        self, ollama_model_tag: str, quant_level: str, prompt: str, max_new_tokens: int
    ) -> RunMetrics:
        import requests

        if quant_level not in SUPPORTED_QUANT_LEVELS:
            raise ValueError(f"Unsupported quant level: {quant_level}")

        # Ollama runs the model in a separate OS process ("llama-server" on this platform;
        # may differ on Linux/macOS builds), not in-process — sample that process's RSS,
        # not ours (see BaseMetricsCollectorMixin docstring for why this matters).
        self._start_ram_sampling(process_name_filter="llama-server")
        wall_start = time.monotonic()
        try:
            self._ensure_available()
            load_start = time.monotonic()
            # Use Ollama's HTTP /api/pull instead of shelling out to the CLI: avoids any
            # dependency on 'ollama' being resolvable on PATH (observed failure in
            # practice: "[WinError 2] The system cannot find the file specified" when
            # the Ollama install directory wasn't on the calling process's PATH).
            self._gatekeeper.execute(
                lambda: requests.post(
                    f"{self._host}/api/pull", json={"model": ollama_model_tag, "stream": False},
                    timeout=1800,
                ).raise_for_status(),
                description=f"ollama pull {ollama_model_tag}",
            )
            load_time = time.monotonic() - load_start

            gen_start = time.monotonic()
            response = self._gatekeeper.execute(
                lambda: requests.post(
                    f"{self._host}/api/generate",
                    json={
                        "model": ollama_model_tag, "prompt": prompt, "stream": False,
                        "options": {"num_predict": max_new_tokens},
                    },
                    timeout=1800,
                ),
                description=f"ollama generate {ollama_model_tag}",
            )
            generation_time = time.monotonic() - gen_start
            payload = response.json()
            generated_text = payload.get("response", "")
            new_tokens = payload.get("eval_count", max_new_tokens)
            tokens_per_sec = new_tokens / generation_time if generation_time > 0 else 0.0

            # Ollama already reports Prefill/Decode timing natively (nanoseconds) —
            # no need for our own streaming measurement here (see PLAN.md ADR-4).
            ttft = payload.get("prompt_eval_duration", 0) / _NANOSECONDS_PER_SECOND
            eval_duration_sec = payload.get("eval_duration", 0) / _NANOSECONDS_PER_SECOND
            tpot = eval_duration_sec / max(new_tokens - 1, 1) if new_tokens > 1 else eval_duration_sec

            total_wall = time.monotonic() - wall_start
            return RunMetrics(
                method="quantized",
                model_name=ollama_model_tag,
                precision_or_quant=quant_level,
                prompt_tokens=payload.get("prompt_eval_count", 0),
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
                method="quantized", model_name=ollama_model_tag, precision_or_quant=quant_level,
                prompt_tokens=0, max_new_tokens=max_new_tokens, succeeded=False, error=str(exc),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
            )
