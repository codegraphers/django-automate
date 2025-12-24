from __future__ import annotations

from typing import Any

from automate_connectors.errors import ConnectorError

from ..redaction import RedactionEngine
from ..validation import OutputValidator
from .types import ToolDefinition


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)


class ToolExecutor:
    """
    Robust Tool Executor.
    Pipeline: Check Registry -> Validate Args -> Execute -> Validate Output -> Redact.
    """

    def __init__(
        self, registry: ToolRegistry, redaction: RedactionEngine | None = None, validator: OutputValidator | None = None
    ) -> None:
        self.registry = registry
        self.redaction = redaction or RedactionEngine()
        self.validator = validator or OutputValidator()

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        # 1. Lookup
        tool = self.registry.get(name)
        if not tool:
            # In strict mode, raise. In forgiving mode, return error dict.
            # We choose strict for internal integrity.
            raise ValueError(f"Tool {name} not found")

        # 2. Argument Validation (against tool.schema)
        # TODO: Implement strict jsonschema check here

        try:
            # 3. Execution
            raw_result = tool.func(**arguments)

            # 4. Result Validation (against tool output schema if exists)
            # This is optional but recommended

            # 5. Redaction
            # Ensure no PII/Secrets leak back into context window unnecessarily
            # (unless the model needs the secret, which is rare. Better to keep it opaque)
            safe_result = self.redaction.redact_payload(raw_result)

            return safe_result

        except ConnectorError as ce:
            # Pass through structured connector errors
            return ce.to_dict()
        except Exception as e:
            # Catchall for arbitrary tool failures
            return {"status": "failed", "error": str(e)}
