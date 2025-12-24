# Writing Rules (JsonLogic)

We use a subset of [JsonLogic](https://jsonlogic.com/) to match events to workflows.

## Supported Operators

### Comparison
*   `==`, `!=`: Equality
*   `>`, `>=`: Numeric comparison
*   `<`, `<=`: Numeric comparison

### Logic
*   `and`: All must be true
*   `or`: At least one true
*   `!`: Not

### Data Access
Use `var` to access event data.
*   `{"var": "type"}` -> `event.type`
*   `{"var": "data.user.id"}` -> `event.payload['data']['user']['id']`

## Examples

**Match specific event type AND high value:**
```json
{
  "and": [
    { "==": [{ "var": "type" }, "order.created"] },
    { ">": [{ "var": "data.amount" }, 1000] }
  ]
}
```

**Match one of a list:**
```json
{
  "in": [{ "var": "data.status" }, ["failed", "error"]]
}
```
