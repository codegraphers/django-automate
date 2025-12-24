from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ErrorInfo:
    """
    Canonical error descriptor used across Governance components.
    Persist this (redacted) for audit/replay/debugging.
    """
    code: str
    message: str
    detail: Optional[str] = None
    retryable: bool = False


class AutomateGovernanceError(Exception):
    """Base exception for governance layer."""


class NotConfiguredError(AutomateGovernanceError):
    """Raised when a required backend or setting is missing."""
