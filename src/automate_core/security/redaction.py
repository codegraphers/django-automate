import re

SENSITIVE_KEYS = {
    "password", "secret", "token", "api_key", "apikey", "access_token",
    "authorization", "private_key", "client_secret"
}

# Regex for common secret patterns
# OpenAI SK: sk-[a-zA-Z0-9]{20,} -> sk-...last4
SK_PATTERN = re.compile(r"sk-[a-zA-Z0-9\-]{20,}")
BEARER_PATTERN = re.compile(r"Bearer\s+(.+)", re.IGNORECASE)

def redact(obj):
    """
    Recursively redact sensitive data from JSON-compatible objects.
    Returns a deep copy.
    """
    if isinstance(obj, dict):
        return _redact_dict(obj)
    elif isinstance(obj, list):
        return [_redact_value(key=None, value=v) for v in obj]
    else:
        return _redact_value(key=None, value=obj)

def _redact_dict(data: dict) -> dict:
    new_data = {}
    for k, v in data.items():
        if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
            new_data[k] = "[REDACTED]"
        else:
            new_data[k] = _redact_value(k, v)
    return new_data

def _redact_value(key, value):
    if isinstance(value, dict):
        return _redact_dict(value)
    elif isinstance(value, list):
        return [_redact_value(key, v) for v in value]
    elif isinstance(value, str):
        return _scrub_string(value)
    else:
        return value

def _scrub_string(text: str) -> str:
    # 1. Check strict known patterns

    # Bearer Token
    match = BEARER_PATTERN.match(text)
    if match:
        return "Bearer [REDACTED]"

    # OpenAI / SK keys
    if SK_PATTERN.search(text):
        def repl(m):
            s = m.group(0)
            return s[:3] + "..." + s[-4:] if len(s) > 7 else "[REDACTED]"
        return SK_PATTERN.sub(repl, text)

    return text
