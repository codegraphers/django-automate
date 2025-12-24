import pytest
from automate.registry import registry
from automate_connectors.adapters.base import ConnectorAdapter as BaseConnector

@pytest.mark.django_db
def test_all_connectors_adhere_to_contract():
    """
    Contract Test Harness: Track D.
    Verifies that EVERY registered connector adheres to the Platform Contract.
    """
    connectors = registry.connectors
    assert len(connectors) > 0, "No connectors registered!"

    for slug, cls in connectors.items():
        print(f"Testing contract for {slug}...")
        
        instance = cls()
        assert isinstance(instance, BaseConnector)
        
        # 1. Check Properties
        assert instance.slug == slug
        assert isinstance(instance.name, str)
        
        # 2. Check Redaction Contract
        sensitive_payload = {"token": "secret123", "data": "ok"}
        redacted = instance.redact(sensitive_payload)
        assert redacted["token"] == "***REDACTED***"
        assert redacted["data"] == "ok"
        
        # 3. Check Validation Contract
        # Should return boolean
        assert isinstance(instance.validate_config({}), bool)
        
        # 4. Check Config Schema existence
        assert isinstance(instance.config_schema, dict)
