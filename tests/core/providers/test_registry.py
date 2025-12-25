import pytest
from django.test import override_settings
from pydantic import BaseModel

from automate_core.providers.base import BaseProvider, CapabilitySpec, ProviderContext
from automate_core.providers.registry import registry


# Dummy Provider
class DummyConfig(BaseModel):
    foo: str

class DummyProvider(BaseProvider):
    key = "dummy"
    display_name = "Dummy Provider"

    @classmethod
    def capabilities(cls):
        return [
            CapabilitySpec(name="test.cap", modalities={"text"}, streaming=False)
        ]

    @classmethod
    def config_schema(cls):
        return DummyConfig

    def __init__(self, config, *, ctx):
        pass

    def normalize_error(self, exc):
        return exc

@pytest.mark.django_db
@override_settings(AUTOMATE_PROVIDERS=["tests.core.providers.test_registry.DummyProvider"])
def test_registry_load_from_settings():
    reg = registry()
    reg.load(force_reload=True)

    provider = reg.get("dummy")
    assert provider is not None
    assert provider.key == "dummy"
    assert provider.cls.__name__ == DummyProvider.__name__

    caps = reg.resolve_for("test.cap")
    assert len(caps) == 1
    assert caps[0].key == "dummy"

def test_registry_empty():
    reg = registry()
    # Force reload with NO settings (or default empty)
    with override_settings(AUTOMATE_PROVIDERS=[]):
        reg.load(force_reload=True)
        assert reg.get("dummy") is None
