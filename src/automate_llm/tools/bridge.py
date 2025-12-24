from __future__ import annotations

from typing import Any

from automate_connectors.errors import ConnectorError
from automate_connectors.execution import ConnectorExecutor


class ConnectorBridgeTool:
    """
    Bridge allowing LLM to call Connector Actions.
    Action: connector.<code_name>.<action_name>
    """

    def __init__(self, executor: ConnectorExecutor):
        self.executor = executor

    def run(
        self, connector_code: str, action: str, profile_name: str, args: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        # 1. Resolve Profile (Stub - normally via Governance/Secrets)
        # In a real app, we'd lookup profile by name + user context
        # resolved_profile = ...
        resolved_profile = {"name": profile_name, "kind": "connector"}  # Placeholder

        try:
            result = self.executor.execute(
                connector_code=connector_code, action=action, profile=resolved_profile, input_args=args, ctx=context
            )
            return {"status": result.status, "data": result.data}
        except ConnectorError as e:
            return e.to_dict()
        except Exception as e:
            return {"status": "failed", "error": str(e)}
