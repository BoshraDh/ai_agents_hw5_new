"""Unit tests for ApiGatekeeper: rate limiting, retry, and queue status."""
from __future__ import annotations

import pytest

from local_llm_bench.shared.gatekeeper import ApiGatekeeper


@pytest.fixture
def gatekeeper() -> ApiGatekeeper:
    return ApiGatekeeper({"requests_per_minute": 100, "max_retries": 3, "retry_after_seconds": 0})


def test_execute_returns_call_result(gatekeeper):
    result = gatekeeper.execute(lambda: 42, description="test call")
    assert result == 42


def test_execute_retries_then_succeeds(gatekeeper):
    attempts = {"count": 0}

    def flaky_call():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ConnectionError("simulated transient failure")
        return "ok"

    result = gatekeeper.execute(flaky_call, description="flaky call")
    assert result == "ok"
    assert attempts["count"] == 2


def test_execute_raises_after_max_retries(gatekeeper):
    def always_fails():
        raise ConnectionError("permanent failure")

    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        gatekeeper.execute(always_fails, description="always fails")


def test_get_queue_status_tracks_calls_in_window(gatekeeper):
    gatekeeper.execute(lambda: None, description="call 1")
    gatekeeper.execute(lambda: None, description="call 2")
    status = gatekeeper.get_queue_status()
    assert status.calls_in_window == 2
    assert status.depth == 0
