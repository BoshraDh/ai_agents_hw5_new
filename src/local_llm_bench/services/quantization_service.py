"""Quantized execution via a local Ollama daemon (GGUF weights, e.g. Q4_K_M / Q2_K)."""
from __future__ import annotations

import subprocess
import time

from local_llm_bench.constants import SUPPORTED_QUANT_LEVELS
from local_llm_bench.shared.gatekeeper import ApiGatekeeper
from local_llm_bench.shared.metrics import BaseMetricsCollectorMixin, RunMetrics


class QuantizationService(BaseMetricsCollectorMixin):
    """Runs a quantized GGUF variant of the model through the local Ollama HTTP API."""

    def __init__(self, gatekeeper: ApiGatekeeper, ollama_host: str):
        self._gatekeeper = gatekeeper
        self._host = ollama_host

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

        self._start_ram_sampling()
        wall_start = time.monotonic()
        try:
            self._ensure_available()
            load_start = time.monotonic()
            self._gatekeeper.execute(
                lambda: subprocess.run(["ollama", "pull", ollama_model_tag], check=True, timeout=1800),
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

            return RunMetrics(
                method="quantized",
                model_name=ollama_model_tag,
                precision_or_quant=quant_level,
                prompt_tokens=payload.get("prompt_eval_count", 0),
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
                method="quantized", model_name=ollama_model_tag, precision_or_quant=quant_level,
                prompt_tokens=0, max_new_tokens=max_new_tokens, succeeded=False, error=str(exc),
                total_wall_time_sec=round(time.monotonic() - wall_start, 3),
            )
