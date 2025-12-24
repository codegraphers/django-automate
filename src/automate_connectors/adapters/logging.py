from typing import Any

from ..adapters.base import ConnectorAdapter, ValidationResult
from ..types import ActionSpec, ConnectorCapabilities, ConnectorResult


class LoggingAdapter(ConnectorAdapter):
    code = "logging"
    name = "Logging"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities()

    @property
    def action_specs(self) -> dict[str, ActionSpec]:
        return {}

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        return ValidationResult(ok=True, errors=[])

    def execute(self, action: str, input_args: dict[str, Any], ctx: dict[str, Any]) -> ConnectorResult:
        # Just return input as output
        return ConnectorResult(data={"logged": True, "input": input_args})

    def normalize_error(self, exc: Exception):
        from ..errors import ConnectorError, ConnectorErrorCode

        return ConnectorError(ConnectorErrorCode.INTERNAL_ERROR, str(exc))
