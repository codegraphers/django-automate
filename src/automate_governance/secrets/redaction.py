from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

DEFAULT_SENSITIVE_KEYS = {
    "api_key",
    "token",
    "secret",
    "password",
    "authorization",
    "cookie",
}


def redact_obj(
    obj: Any,
    *,
    sensitive_keys: Iterable[str] = DEFAULT_SENSITIVE_KEYS,
    mask: str = "****",
    max_value_len: int = 128,
) -> Any:
    """
    Redact values in mappings/lists by key name heuristics.

    Best practice:
    - Call this at all enforcement points: logs, admin serializers, persistence.
    """
    sk = {k.lower() for k in sensitive_keys}

    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            ks = str(k).lower()
            if any(s in ks for s in sk):
                out[k] = mask
            else:
                out[k] = redact_obj(v, sensitive_keys=sk, mask=mask, max_value_len=max_value_len)
        return out

    if isinstance(obj, list):
        return [redact_obj(x, sensitive_keys=sk, mask=mask, max_value_len=max_value_len) for x in obj]

    if isinstance(obj, str) and len(obj) > max_value_len:
        return obj[:max_value_len] + "…"

    return obj
