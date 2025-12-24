# Connector Adapter Contract

To build a connector, inherit from `automate_connectors.adapters.base.ConnectorAdapter`.

## Class Attributes
*   `code` (str): Unique snake_case identifier (e.g., `slack`).
*   `name` (str): Human-readable name.
*   `actions` (dict): Map of `action_slug` -> `ActionSpec`.

## Methods

### `execute(self, action, params, context)`
**Arguments**:
*   `action` (str): The specific operation (e.g., `post_message`).
*   `params` (dict): The resolved input parameters (Jinja2 templates already rendered).
*   `context` (dict): Contains `secrets` (dict of resolved secrets) and `trace_id`.

**Returns**:
*   `dict` or `None`. The output payload.

**Raises**:
*   `ConnectorError`: For managed failures (retried).
*   `Exception`: Unmanaged failures (also retried).

## Testing
Use `automate_testing.contracts.ConnectorContractTest` to verify your implementation follows the spec.
