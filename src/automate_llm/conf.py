from typing import Any

from django.conf import settings

DEFAULTS: dict[str, Any] = {
    "DEFAULT_PROVIDER_PROFILE": "llm:default",
    "DEFAULT_MODEL": "gpt-4.1-mini",
    "TIMEOUT_S": 60,
    "RETRY": {"max_attempts": 3, "base_backoff_s": 1.0, "max_backoff_s": 20.0},
    "STREAMING_ENABLED": True,
    "BUDGETS": {"max_cost_usd_per_run": 0.25, "max_tokens_per_run": 8000, "max_prompt_chars": 80_000},
    "POLICY": {
        "model_allowlist": [],
        "tool_allowlist": [],
        "allow_raw_payload_storage": False,
        "redaction": {"enabled": True, "modes": ["secrets"], "max_field_len": 2000},
        "output_contract": {"require_json_schema": False, "max_json_depth": 30},
    },
    "DB_OPT": {"enable_json_indexes_if_supported": True, "enable_gin_if_postgres": True},
}


def llm_settings() -> dict[str, Any]:
    root = getattr(settings, "DJANGO_AUTOMATE", {}) or {}
    llm = root.get("LLM", {}) or {}
    merged = {**DEFAULTS, **llm}

    # shallow merge for nested dicts
    for k in ("RETRY", "BUDGETS", "POLICY", "DB_OPT"):
        merged[k] = {**DEFAULTS.get(k, {}), **llm.get(k, {})}

    # nested redaction/output_contract
    merged["POLICY"]["redaction"] = {**DEFAULTS["POLICY"]["redaction"], **merged["POLICY"].get("redaction", {})}
    merged["POLICY"]["output_contract"] = {
        **DEFAULTS["POLICY"]["output_contract"],
        **merged["POLICY"].get("output_contract", {}),
    }
    return merged
