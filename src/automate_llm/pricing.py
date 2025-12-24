from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceRate:
    input_usd_per_1k: float
    output_usd_per_1k: float
    min_tokens: int = 0

# Static fallback table
_STATIC_PRICING_TABLE: dict[str, PriceRate] = {
    "gpt-4o-mini": PriceRate(0.00015, 0.0006),
    "gpt-4o": PriceRate(0.0025, 0.01),
    "claude-3-5-sonnet": PriceRate(0.003, 0.015),
}

class ModelPricing:
    """
    Source of Truth for pricing.
    Backwards compatible with static table, forward compatible with DB overrides.
    """

    def get_rate(self, model: str, provider: str) -> PriceRate | None:
        # TODO: Lookup DB override first

        # Fallback to static table
        # Normalize model name slightly
        key = model.lower()
        for known_key, rate in _STATIC_PRICING_TABLE.items():
            if known_key in key:
                 return rate

        return None

    def calculate_cost(self, model: str, tokens_in: int, tokens_out: int, provider: str = "") -> float:
        rate = self.get_rate(model, provider)
        if not rate:
            return 0.0

        cost = (tokens_in / 1000.0) * rate.input_usd_per_1k
        cost += (tokens_out / 1000.0) * rate.output_usd_per_1k
        return round(cost, 6)
