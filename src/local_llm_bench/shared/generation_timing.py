"""Streaming-based TTFT/TPOT measurement, shared by services whose models expose a
Hugging Face-compatible .generate(streamer=...) call (ModelLoaderService, AirllmService).

A single generate() call cannot distinguish Prefill (TTFT) from Decode (TPOT) latency —
only per-token arrival timestamps can, hence the streaming approach (see PLAN.md ADR-4).
"""
from __future__ import annotations

import threading
import time
from typing import Callable


class StreamingTimingMixin:
    """Runs generate() on a background thread while timing token arrivals on the caller thread."""

    def _generate_with_timing(
        self, generate_fn: Callable, streamer, generate_kwargs: dict, max_new_tokens: int
    ) -> tuple[str, float, float, int]:
        """Returns (generated_text, ttft_sec, tpot_sec, token_count)."""
        thread = threading.Thread(
            target=generate_fn, kwargs={**generate_kwargs, "streamer": streamer,
                                         "max_new_tokens": max_new_tokens},
            daemon=True,
        )
        start = time.monotonic()
        thread.start()

        token_timestamps: list[float] = []
        generated_text = ""
        for chunk in streamer:
            token_timestamps.append(time.monotonic())
            generated_text += chunk
        thread.join(timeout=1.0)

        if not token_timestamps:
            return generated_text, 0.0, 0.0, 0

        ttft = token_timestamps[0] - start
        if len(token_timestamps) > 1:
            gaps = [b - a for a, b in zip(token_timestamps, token_timestamps[1:])]
            tpot = sum(gaps) / len(gaps)
        else:
            tpot = 0.0
        return generated_text, ttft, tpot, len(token_timestamps)
