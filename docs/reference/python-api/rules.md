# Rules API

Located in `django_automate.rules`.

## `evaluate(rule, data)`
Evaluates a single rule against a data dictionary.
*   **Args**:
    *   `rule` (dict): JsonLogic structure.
    *   `data` (dict): The event payload / context.
*   **Returns**: `bool` (Match or No Match).

## `explain(rule, data)`
Debugs a rule execution. Returns a tree where every node is annotated with its result.
*   **Returns**: `ExplainNode` (dict).
    ```json
    {
        "operator": "and",
        "result": false,
        "children": [
            { "operator": "==", "result": true },
            { "operator": ">", "result": false, "reason": "50 < 100" }
        ]
    }
    ```
