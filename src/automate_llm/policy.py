from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .conf import llm_settings
from .errors import LLMError, LLMErrorCode
from .types import ChatRequest, CostEstimate, ToolSpec


@dataclass(frozen=True)
class EffectivePolicy:
    provider: str
    model: str
    timeout_s: int
    retry: dict[str, Any]
    budgets: dict[str, Any]
    policy: dict[str, Any]

class LLMPolicyEngine:
    """
    Merge and enforce policy:
      settings defaults -> provider profile -> prompt version -> request overrides -> clamp
    """

    def merge(
        self,
        *,
        provider: str,
        model: str,
        provider_profile_cfg: dict[str, Any],
        prompt_defaults: dict[str, Any],
        request_overrides: dict[str, Any],
    ) -> EffectivePolicy:
        base = llm_settings()

        # Policy Merge Strategy:
        # 1. Base Settings
        # 2. Provider Profile (from DB/Settings)
        # 3. Prompt Defaults (from compiled prompt)
        # 4. Request Overrides (runtime)

        # Helper for dict merging
        def merge_d(k: str) -> dict[str, Any]:
            b = base.get(k, {}) or {}
            pp = provider_profile_cfg.get(k, {}) or {}
            pd = prompt_defaults.get(k, {}) or {}
            ro = request_overrides.get(k, {}) or {}
            return {**b, **pp, **pd, **ro}

        merged_retry = merge_d("RETRY")
        merged_budgets = merge_d("BUDGETS")
        merged_policy = merge_d("POLICY")

        timeout = int(provider_profile_cfg.get("timeout_s", base["TIMEOUT_S"]))

        return EffectivePolicy(
            provider=provider,
            model=model,
            timeout_s=timeout,
            retry=merged_retry,
            budgets=merged_budgets,
            policy=merged_policy,
        )

    def enforce_request(self, req: ChatRequest, eff: EffectivePolicy, tools: list[ToolSpec]) -> None:
        allow_models = eff.policy.get("model_allowlist") or []
        if allow_models and req.model not in allow_models:
            raise LLMError(
                code=LLMErrorCode.POLICY_VIOLATION,
                message_safe=f"Model not allowed: {req.model}",
                retryable=False,
                details_safe={"allowed": allow_models},
            )

        allow_tools = eff.policy.get("tool_allowlist") or []
        if allow_tools:
            for t in tools:
                if t.name not in allow_tools:
                    raise LLMError(
                        code=LLMErrorCode.POLICY_VIOLATION,
                        message_safe=f"Tool not allowed: {t.name}",
                        retryable=False,
                        details_safe={"allowed": allow_tools},
                    )

        # Clamp max tokens if provided
        max_tokens_cap = eff.budgets.get("max_tokens_per_run")
        if max_tokens_cap is not None and req.max_tokens is not None and req.max_tokens > int(max_tokens_cap):
            raise LLMError(
                code=LLMErrorCode.POLICY_VIOLATION,
                message_safe="max_tokens exceeds budget cap",
                retryable=False,
                details_safe={"cap": max_tokens_cap, "requested": req.max_tokens},
            )

    def enforce_budget_estimate(self, est: CostEstimate, eff: EffectivePolicy) -> None:
        max_cost = eff.budgets.get("max_cost_usd_per_run")
        if max_cost is not None and est.estimated_cost > float(max_cost):
            raise LLMError(
                code=LLMErrorCode.POLICY_VIOLATION,
                message_safe="Estimated cost exceeds budget cap",
                retryable=False,
                details_safe={"cap": max_cost, "estimated": est.estimated_cost},
            )
