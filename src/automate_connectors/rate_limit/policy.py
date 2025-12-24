from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Literal

@dataclass(frozen=True)
class RateLimitPolicy:
    mode: Literal["static", "dynamic"] = "static"
    requests_per_minute:  Optional[int] = None
    burst: Optional[int] = None # For token bucket
    header_overrides: Dict[str, str] = field(default_factory=lambda: {
        "limit": "X-RateLimit-Limit",
        "remaining": "X-RateLimit-Remaining",
        "retry_after": "Retry-After"
    })
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RateLimitPolicy:
         # Basic factory
         return cls(
             mode=data.get("mode", "static"),
             requests_per_minute=data.get("requests_per_minute"),
             burst=data.get("burst"),
             header_overrides=data.get("header_overrides", {})
         )
