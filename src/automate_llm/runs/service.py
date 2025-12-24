from __future__ import annotations

from typing import Any

from ..conf import llm_settings
from ..errors import LLMError, LLMErrorCode
from ..policy import LLMPolicyEngine
from ..prompts.compiler import PromptCompiler, PromptVersionSnapshot
from ..redaction import RedactionEngine
from .executor import RunExecutor
from .store import RunStore

# Secrets Integration
# Avoid top-level model imports to prevent AppRegistryNotReady during startup
SecretResolver = None
ConnectionProfile = None

_DEFAULT_STORE: RunStore | None = None


class RunService:
    def __init__(
        self,
        *,
        store: RunStore,
        compiler: PromptCompiler | None = None,
        executor: RunExecutor | None = None,
        policy: LLMPolicyEngine | None = None,
        redaction: RedactionEngine | None = None,
        secret_resolver: Any | None = None,
    ) -> None:
        self.store = store
        self.compiler = compiler or PromptCompiler()
        self.executor = executor or RunExecutor()
        self.policy = policy or LLMPolicyEngine()
        self.redaction = redaction or RedactionEngine()
        self.secret_resolver = secret_resolver

        # Lazy load secret resolver if not provided
        if not self.secret_resolver:
            try:
                from automate_governance.secrets.resolver import SecretResolver as Resolver

                self.secret_resolver = Resolver()
            except ImportError:
                pass

    def create_run(
        self,
        *,
        prompt_ver: PromptVersionSnapshot | None,
        raw_messages: Any | None,
        inputs: dict[str, Any] | None,
        provider_profile: str,
        request_overrides: dict[str, Any],
        trace_id: str | None,
        idempotency_key: str | None,
        mode: str,
    ) -> dict[str, Any]:
        payload = {
            "prompt_key": prompt_ver.prompt_key if prompt_ver else None,
            "prompt_version": prompt_ver.version if prompt_ver else None,
            "provider_profile": provider_profile,
            "trace_id": trace_id,
            "mode": mode,
            "status": "queued" if mode == "async" else "running",
            "request_overrides": request_overrides,
        }
        # Always store a redacted copy for audit-safe visibility
        payload["request_redacted_json"] = self.redaction.redact_payload(
            {"inputs": inputs, "raw_messages": raw_messages}
        )
        return self.store.create_run(payload, idempotency_key=idempotency_key)

    def execute_sync(
        self,
        *,
        run_id: int,
        provider_profile: str,  # passed from create_run context usually
        model: str,
        prompt_ver: PromptVersionSnapshot | None,
        inputs: dict[str, Any] | None,
        raw_messages: Any | None,
        request_overrides: dict[str, Any],
        trace_id: str | None,
    ) -> dict[str, Any]:
        self.store.mark_running(run_id)

        try:
            # 1. Resolve Provider Profile & Secrets
            # Convention: provider_profile string match a ConnectionProfile.name in DB
            # If not found, fall back to settings or error.

            provider_code = "openai"  # Default fallback
            api_key = ""
            provider_cfg = {}

            # Lazy import model to avoid AppRegistryNotReady
            try:
                from automate_governance.models import ConnectionProfile as conn_profile_model
            except ImportError:
                conn_profile_model = None

            if self.secret_resolver and conn_profile_model:
                # Lookup profile
                try:
                    profile = conn_profile_model.objects.get(name=provider_profile)
                    # Resolve secrets
                    resolved = self.secret_resolver.resolve_dictionary(profile.secrets)
                    # Merge config
                    self.runtime_config.update(resolved)
                    provider_cfg = profile.config or {}
                    provider_code = provider_cfg.get("provider", "openai")
                except conn_profile_model.DoesNotExist:
                    # Check settings.LLM.PROVIDERS for static config (legacy/dev mode)
                    pass

            # Simple fallback for skeleton if no DB profile found (e.g. initial dev)
            if not api_key:
                # Attempt to load from settings directly (e.g. AUTOMATE.LLM.PROFILES)
                # keeping it simple for now, assume openai
                pass

            # 2. Compile Prompt
            if prompt_ver:
                compiled = self.compiler.compile(
                    provider=provider_code,
                    model=model,
                    prompt_ver=prompt_ver,
                    inputs=inputs or {},
                    timeout_s=int(provider_cfg.get("timeout_s", llm_settings()["TIMEOUT_S"])),
                    trace_id=trace_id,
                )
                req = compiled.request
                prompt_defaults = {"policy": prompt_ver.policy_hints_json or {}}
            else:
                # raw mode placeholder
                raise NotImplementedError("raw_messages mode not implemented in skeleton")

            # 3. Policy Merge
            eff = self.policy.merge(
                provider=provider_code,
                model=model,
                provider_profile_cfg=provider_cfg,
                prompt_defaults=prompt_defaults,
                request_overrides=request_overrides,
            )

            # 4. Execute
            resp = self.executor.execute(
                provider_code=provider_code,
                api_key=api_key,
                req=req,
                effective_policy=eff,
                adapter_cfg=provider_cfg,
            )

            # 5. Success
            result = {
                "status": "succeeded",
                "response_redacted_json": self.redaction.redact_payload(
                    {"output_text": resp.output_text, "tool_calls": [tc.__dict__ for tc in resp.tool_calls]}
                ),
                "usage_json": {
                    "tokens_in": resp.usage.tokens_in,
                    "tokens_out": resp.usage.tokens_out,
                    "total_tokens": resp.usage.total_tokens,
                    "cost_usd": resp.usage.cost_usd,
                    "provider_request_id": resp.usage.provider_request_id,
                },
            }
            self.store.mark_succeeded(run_id, result)
            return self.store.get_run(run_id)

        except LLMError as e:
            err = {"status": "failed", "error": e.to_error_dict()}
            self.store.mark_failed(run_id, err)
            return self.store.get_run(run_id)
        except Exception as exc:
            e = LLMError(code=LLMErrorCode.INTERNAL_ERROR, message_safe=str(exc), retryable=False)
            err = {"status": "failed", "error": e.to_error_dict()}
            self.store.mark_failed(run_id, err)
            return self.store.get_run(run_id)

    def enqueue_async(self, *, run_id: int) -> None:
        # TODO: integrate with Outbox (preferred) and/or Celery
        raise NotImplementedError


# Convenience functions
def llm_call(**kwargs: Any) -> Any:
    raise NotImplementedError


def llm_run_async(**kwargs: Any) -> Any:
    raise NotImplementedError
