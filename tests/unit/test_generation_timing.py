"""Unit tests for StreamingTimingMixin (TTFT/TPOT measurement, PLAN.md ADR-4)."""
from __future__ import annotations

from local_llm_bench.shared.generation_timing import StreamingTimingMixin


class _FakeStreamer:
    def __init__(self, chunks: list[str]):
        self._chunks = chunks

    def __iter__(self):
        yield from self._chunks


class _Collector(StreamingTimingMixin):
    pass


def test_generate_with_timing_returns_text_and_positive_metrics():
    collector = _Collector()
    streamer = _FakeStreamer(["a", "b", "c"])

    text, ttft, tpot, count = collector._generate_with_timing(
        lambda **kwargs: None, streamer, {}, 3,
    )

    assert text == "abc"
    assert count == 3
    assert ttft >= 0
    assert tpot >= 0


def test_generate_with_timing_handles_single_token():
    collector = _Collector()
    streamer = _FakeStreamer(["only"])

    text, ttft, tpot, count = collector._generate_with_timing(
        lambda **kwargs: None, streamer, {}, 1,
    )

    assert text == "only"
    assert count == 1
    assert tpot == 0.0


def test_generate_with_timing_handles_empty_stream():
    collector = _Collector()
    streamer = _FakeStreamer([])

    text, ttft, tpot, count = collector._generate_with_timing(
        lambda **kwargs: None, streamer, {}, 0,
    )

    assert text == ""
    assert count == 0
    assert ttft == 0.0
    assert tpot == 0.0
