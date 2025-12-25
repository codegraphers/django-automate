import pytest

from automate_core.security.redaction import redact


def test_redact_flat_dict():
    data = {"name": "foo", "password": "s3cret", "api_key": "sk-12345"}
    redacted = redact(data)
    assert redacted["name"] == "foo"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"

def test_redact_nested_dict():
    data = {
        "config": {
            "auth": {
                "token": "sensitive"
            }
        }
    }
    redacted = redact(data)
    assert redacted["config"]["auth"]["token"] == "[REDACTED]"

def test_redact_list():
    data = [{"name": "foo"}, {"token": "bar"}]
    redacted = redact(data)
    assert redacted[0]["name"] == "foo"
    assert redacted[1]["token"] == "[REDACTED]"

def test_redact_regex_bearer():
    # Structural redaction for common header patterns
    data = {"Authorization": "Bearer some-token-value"}
    redacted = redact(data)
    assert redacted["Authorization"] == "[REDACTED]"

def test_redact_pattern_sk():
    # OpenAI style keys in arbitrary fields
    data = {"some_field": "sk-proj-1234567890abcdef"}
    redacted = redact(data)
    assert redacted["some_field"] == "sk-...cdef" # Structural redaction preference

def test_determinism():
    # Should not mutate original
    data = {"password": "foo"}
    redacted = redact(data)
    assert data["password"] == "foo"
    assert redacted["password"] == "[REDACTED]"
