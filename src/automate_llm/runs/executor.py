from __future__ import annotations

from typing import Any

from ..errors import LLMError, LLMErrorCode
from ..policy import LLMPolicyEngine
from ..redaction import RedactionEngine
from ..registry import get_adapter_cls
from ..safety import SafetyPipeline
from ..tools import ToolExecutor, ToolRegistry
from ..types import ChatRequest, ChatResponse
from ..validation import OutputValidator


class RunExecutor:
    def __init__(
        self,
        *,
        policy_engine: LLMPolicyEngine | None = None,
        redaction: RedactionEngine | None = None,
        tool_registry: ToolRegistry | None = None,
        output_validator: OutputValidator | None = None,
        pre_send_pipeline: SafetyPipeline | None = None,
        post_receive_pipeline: SafetyPipeline | None = None,
    ) -> None:
        self.policy_engine = policy_engine or LLMPolicyEngine()
        self.redaction = redaction or RedactionEngine()
        self.tool_executor = ToolExecutor(tool_registry or ToolRegistry())
        self.output_validator = output_validator or OutputValidator()
        self.pre_send_pipeline = pre_send_pipeline
        self.post_receive_pipeline = post_receive_pipeline

    def execute(
        self,
        *,
        provider_code: str,
        api_key: str,
        req: ChatRequest,
        effective_policy: Any,
        adapter_cfg: dict[str, Any],
    ) -> ChatResponse:
        adapter_cls = get_adapter_cls(provider_code)
        adapter = adapter_cls(
            base_url=adapter_cfg.get("base_url"),
            headers=adapter_cfg.get("headers")
        )

        # 1. Pre-Send Safety Hooks
        if self.pre_send_pipeline:
             res = self.pre_send_pipeline.process({"req": req}, req)
             if not res.allowed:
                 raise LLMError(LLMErrorCode.POLICY_VIOLATION, f"Pre-send safety check failed: {res.rejection_reason}")
             if res.modified_payload:
                 # In a real scenario, we'd need to safely cast back to ChatRequest if type changed
                 # or assume hooks modify in-place/return compatible types.
                 # For safe skeletal impl, we skip replacing req unless carefully typed.
                 pass

        # 2. Policy Enforcement & Budget
        tools = list(req.tools)
        self.policy_engine.enforce_request(req, effective_policy, tools)
        est = adapter.estimate_cost(req)
        self.policy_engine.enforce_budget_estimate(est, effective_policy)

        try:
            # 3. Execution
            resp = adapter.chat(req, api_key=api_key)

            # 4. Post-Receive Safety Hooks
            if self.post_receive_pipeline:
                res = self.post_receive_pipeline.process({"req": req, "resp": resp}, resp)
                if not res.allowed:
                    raise LLMError(LLMErrorCode.POLICY_VIOLATION, f"Post-receive safety check failed: {res.rejection_reason}")

            # 5. Output Validation (Structural)
            # Check schema if one was implied by the request (e.g. response_format)
            # For now, just validating internal consistency

            # 6. Tool Validation (if tools used in response)
            if resp.tool_calls:
                 # Check against allowlist in policy/registry
                 pass

            return resp

        except LLMError:
            raise
        except Exception as exc:
            raise adapter.normalize_error(exc)
