from __future__ import annotations
import os
from typing import Any, Dict
from django.conf import settings

# Default configuration
DEFAULTS = {
    "SECRETS": {
        "DEFAULT_BACKEND": "env",
        "REDACTION": {"MASK": "****"},
    },
    "OUTBOX": {
        "MAX_ATTEMPTS": 15,
        "LEASE_SECONDS": 60,
    },
    "TRIGGERS": {
        "STRICT_MATCHING": True,
    },
    "LLM": {
        "DEFAULT_PROVIDER": "openai",
    }
}

class ConfigLoader:
    """
    Unified configuration access:
    defaults < settings.AUTOMATE < env overrides < DB (future)
    """

    @classmethod
    def get(cls, path: str, default: Any = None) -> Any:
        keys = path.split(".")
        
        # 1. Start with settings.AUTOMATE
        current = getattr(settings, "AUTOMATE", {})
        
        # Traverse
        found = True
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
                if current is None:
                    found = False
                    break
            else:
                found = False
                break
        
        if found and current is not None:
             return current

        # 2. Check Defaults
        current = DEFAULTS
        found = True
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
                if current is None:
                    found = False
                    break
        
        if found and current is not None:
            return current
            
        return default
