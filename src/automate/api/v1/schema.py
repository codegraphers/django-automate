
# Standard Error Schema Definition for reuse
STANDARD_ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "correlation_id": {"type": "string", "format": "uuid"},
            },
            "required": ["code", "message"]
        }
    }
}
