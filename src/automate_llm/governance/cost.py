# Simple hardcoded pricing table for MVP
# In production, fetch from DB or external service
PRICING_TABLE_USD_PER_1K = {
    "gpt-4-turbo": (0.01, 0.03),  # (Input, Output)
    "gpt-3.5-turbo": (0.001, 0.002),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-sonnet": (0.003, 0.015),
}


class CostTracker:
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        # Fuzzy match or exact match model name
        pricing = PRICING_TABLE_USD_PER_1K.get(model)
        if not pricing:
            # Fallback for unknown models (safe default 0 or high?)
            # Log warning
            return 0.0

        rate_in, rate_out = pricing
        cost = (input_tokens / 1000 * rate_in) + (output_tokens / 1000 * rate_out)
        return round(cost, 6)

    def check_budget(self, tenant_id: str, estimated_cost: float) -> bool:
        """
        Check if tenant has sufficient budget.
        Stub: Always True for now.
        Real impl: Atomic decrement of daily budget in Redis/DB.
        """
        return True
