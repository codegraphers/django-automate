from __future__ import annotations

import sys
from importlib.metadata import entry_points

from .base import Registry, T


def autodiscover(registry: Registry[T], group: str) -> None:
    """
    Populate registry from entry_points.
    """
    # Defensive for different python versions of importlib.metadata
    eps = entry_points()
    if sys.version_info >= (3, 10) and hasattr(eps, "select"):
        # 3.10+ API
        matches = eps.select(group=group)
    else:
        # Fallback (older API returns dict-like or list)
        matches = eps.get(group, [])

    for ep in matches:
        try:
            cls = ep.load()
            registry.register(ep.name, cls)
        except Exception as e:
            # Log failure but don't crash startup
            print(f"Failed to load plugin {ep.name}: {e}")
