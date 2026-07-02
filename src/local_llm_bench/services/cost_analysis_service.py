"""Economic feasibility analysis: On-Prem vs. third-party API (ex05 section 5.5, MANDATORY).

Computes cost-per-request for both approaches across a range of monthly usage volumes
and locates the break-even point where On-Prem becomes cheaper. All prices/assumptions
come from config/economic_assumptions.json — nothing is hardcoded here.
"""
from __future__ import annotations

from dataclasses import dataclass

_SECONDS_PER_HOUR = 3600.0
_WATT_HOURS_PER_KWH = 1000.0


@dataclass
class BreakevenResult:
    usage_volumes: list[int]
    api_costs: list[float]
    onprem_costs: list[float]
    breakeven_volume: int | None
    assumptions: dict


class CostAnalysisService:
    """Computes API vs. On-Prem cost curves and the break-even monthly usage volume."""

    def __init__(self, assumptions: dict):
        self._validate(assumptions)
        self._assumptions = assumptions

    @staticmethod
    def _validate(assumptions: dict) -> None:
        on_prem = assumptions["on_prem"]
        if on_prem["hardware_lifespan_years"] <= 0:
            raise ValueError("hardware_lifespan_years must be > 0")
        if on_prem["hardware_cost_usd"] < 0 or on_prem["electricity_price_usd_per_kwh"] < 0:
            raise ValueError("on_prem costs must be non-negative")

    def estimate_api_cost_per_request(self, input_tokens: int, output_tokens: int) -> float:
        pricing = self._assumptions["api_pricing"]
        discount = pricing.get("cached_token_discount_ratio", 0.0)
        effective_input_tokens = input_tokens * (1 - discount)
        input_cost = (effective_input_tokens / 1000) * pricing["price_per_1k_input_tokens_usd"]
        output_cost = (output_tokens / 1000) * pricing["price_per_1k_output_tokens_usd"]
        return input_cost + output_cost

    def estimate_onprem_cost_per_month(
        self, requests_per_month: int, assumed_tdp_watts: float, avg_run_seconds_per_request: float,
    ) -> float:
        on_prem = self._assumptions["on_prem"]
        capex_per_month = on_prem["hardware_cost_usd"] / (on_prem["hardware_lifespan_years"] * 12)
        maintenance_per_month = on_prem["annual_maintenance_usd"] / 12
        energy_kwh = (
            assumed_tdp_watts * avg_run_seconds_per_request * requests_per_month
        ) / (_SECONDS_PER_HOUR * _WATT_HOURS_PER_KWH)
        electricity_cost = energy_kwh * on_prem["electricity_price_usd_per_kwh"]
        return capex_per_month + maintenance_per_month + electricity_cost

    def find_breakeven(self, assumed_tdp_watts: float, avg_run_seconds_per_request: float) -> BreakevenResult:
        scenario = self._assumptions["usage_scenario"]
        volumes = scenario["usage_volumes_per_month"]
        per_request_api_cost = self.estimate_api_cost_per_request(
            scenario["avg_input_tokens_per_request"], scenario["avg_output_tokens_per_request"],
        )

        api_costs = [per_request_api_cost * v for v in volumes]
        onprem_costs = [
            self.estimate_onprem_cost_per_month(v, assumed_tdp_watts, avg_run_seconds_per_request)
            for v in volumes
        ]

        breakeven_volume = next(
            (v for v, api, onprem in zip(volumes, api_costs, onprem_costs, strict=True) if onprem <= api),
            None,
        )

        return BreakevenResult(
            usage_volumes=volumes, api_costs=api_costs, onprem_costs=onprem_costs,
            breakeven_volume=breakeven_volume, assumptions=self._assumptions,
        )
