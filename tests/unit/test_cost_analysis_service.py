"""Unit tests for CostAnalysisService (ex05 section 5.5 — mandatory economic analysis)."""
from __future__ import annotations

import pytest

from local_llm_bench.services.cost_analysis_service import CostAnalysisService


def _assumptions(**overrides) -> dict:
    base = {
        "api_pricing": {
            "price_per_1k_input_tokens_usd": 0.03,
            "price_per_1k_output_tokens_usd": 0.06,
            "cached_token_discount_ratio": 0.0,
        },
        "on_prem": {
            "hardware_cost_usd": 1200.0,
            "hardware_lifespan_years": 2,
            "electricity_price_usd_per_kwh": 0.2,
            "annual_maintenance_usd": 0.0,
        },
        "usage_scenario": {
            "avg_input_tokens_per_request": 1000,
            "avg_output_tokens_per_request": 500,
            "usage_volumes_per_month": [1, 10, 100, 1000, 10000, 100000],
        },
    }
    base.update(overrides)
    return base


def test_estimate_api_cost_per_request():
    service = CostAnalysisService(_assumptions())
    cost = service.estimate_api_cost_per_request(1000, 500)
    assert cost == pytest.approx(0.03 + 0.03, abs=1e-6)


def test_estimate_api_cost_applies_caching_discount():
    assumptions = _assumptions()
    assumptions["api_pricing"]["cached_token_discount_ratio"] = 0.5
    service = CostAnalysisService(assumptions)
    cost = service.estimate_api_cost_per_request(1000, 500)
    assert cost == pytest.approx(0.015 + 0.03, abs=1e-6)


def test_estimate_onprem_cost_per_month_includes_capex():
    service = CostAnalysisService(_assumptions())
    cost = service.estimate_onprem_cost_per_month(
        requests_per_month=100, assumed_tdp_watts=28.0, avg_run_seconds_per_request=10.0,
    )
    expected_capex = 1200.0 / (2 * 12)
    assert cost >= expected_capex


def test_find_breakeven_returns_none_when_onprem_always_pricier():
    assumptions = _assumptions()
    assumptions["on_prem"]["hardware_cost_usd"] = 1_000_000.0
    service = CostAnalysisService(assumptions)
    result = service.find_breakeven(assumed_tdp_watts=28.0, avg_run_seconds_per_request=1.0)
    assert result.breakeven_volume is None


def test_find_breakeven_finds_crossover_point():
    assumptions = _assumptions()
    assumptions["on_prem"]["hardware_cost_usd"] = 50.0
    assumptions["on_prem"]["hardware_lifespan_years"] = 1
    service = CostAnalysisService(assumptions)
    result = service.find_breakeven(assumed_tdp_watts=28.0, avg_run_seconds_per_request=1.0)
    assert result.breakeven_volume is not None
    assert result.breakeven_volume in result.usage_volumes


def test_init_rejects_invalid_lifespan():
    assumptions = _assumptions()
    assumptions["on_prem"]["hardware_lifespan_years"] = 0
    with pytest.raises(ValueError, match="lifespan"):
        CostAnalysisService(assumptions)


def test_init_rejects_negative_cost():
    assumptions = _assumptions()
    assumptions["on_prem"]["hardware_cost_usd"] = -1.0
    with pytest.raises(ValueError, match="non-negative"):
        CostAnalysisService(assumptions)
