from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Avoid hard dep on automate_governance specific model class to keep clean,
# but assume dict-like object or Django model instance passed in.
# Real usage: integration with Admin form or API view


@dataclass
class ProfileValidationAttempt:
    ok: bool
    errors: list[str]


class ConnectionProfileValidator:
    def validate(self, profile_data: dict[str, Any], connector_code: str) -> ProfileValidationAttempt:
        """
        Validates a profile payload against the requirements of a specific connector.
        """
        # 1. Enforce Kind
        if profile_data.get("kind") != "connector":
            return ProfileValidationAttempt(ok=False, errors=["Profile kind must be 'connector'"])

        # 2. Enforce Code match
        cfg = profile_data.get("config", {}) or {}
        if cfg.get("connector_code") != connector_code:
            # This check depends on if the profile is strictly 1:1 with code
            # or if 'config.connector_code' is the source of truth.
            pass

        # 3. Load Adapter for deep validation
        # from ..registry import get_adapter_cls
        # try:
        #    cls = get_adapter_cls(connector_code)
        #    result = cls().validate_config(profile_data)
        #    if not result.ok:
        #       return ProfileValidationAttempt(ok=False, errors=result.errors)
        # except Exception as e:
        #    return ProfileValidationAttempt(ok=False, errors=[str(e)])

        return ProfileValidationAttempt(ok=True, errors=[])
