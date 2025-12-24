from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorInfo:
    """
    Canonical error descriptor used across Governance components.
    Persist this (redacted) for audit/replay/debugging.
    """
    code: str
    message: str
    detail: str | None = None
    retryable: bool = False


class AutomateGovernanceError(Exception):
    """Base exception for governance layer."""


class NotConfiguredError(AutomateGovernanceError):
    """Raised when a required backend or setting is missing."""
