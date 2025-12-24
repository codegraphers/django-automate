from __future__ import annotations
from typing import List, Dict, Any
from django.conf import settings

# Default Configuration
_DEFAULT_INTEROP = {
    "ENABLED": False,
    "ORCHESTRATORS_ENABLED": ["n8n"],
    "DEFAULT_ORCHESTRATOR_INSTANCE": "n8n:primary",
    "N8N_INSTANCES": {},
    "TEMPLATES_HOST_ENABLED": False,
    "SYNC_ENABLED": False,
}

def get_interop_setting(key: str, default: Any = None) -> Any:
    interop_conf = getattr(settings, "AUTOMATE_INTEROP", {})
    return interop_conf.get(key, _DEFAULT_INTEROP.get(key, default))

class InteropFlags:
    @property
    def is_enabled(self) -> bool:
        return get_interop_setting("ENABLED", False)

    @property
    def enabled_orchestrators(self) -> List[str]:
        return get_interop_setting("ORCHESTRATORS_ENABLED", [])

    @property
    def templates_host_enabled(self) -> bool:
        return get_interop_setting("TEMPLATES_HOST_ENABLED", False)

    @property
    def sync_enabled(self) -> bool:
        return get_interop_setting("SYNC_ENABLED", False)

flags = InteropFlags()
