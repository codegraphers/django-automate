from __future__ import annotations

from typing import Any

import pytest

from .adapters.base import ConnectorAdapter
from .errors import ConnectorError, ConnectorErrorCode


class ConnectorContractHarness:
    """
    Standard test suite for any ConnectorAdapter.
    """

    @pytest.fixture
    def adapter_cls(self) -> type[ConnectorAdapter]:
        raise NotImplementedError("Must provide adapter_cls")

    @pytest.fixture
    def valid_config(self) -> dict[str, Any]:
        return {}

    def test_capabilities_schema(self, adapter_cls):
        """Ensure capabilities returns valid flags"""
        adapter = adapter_cls()
        caps = adapter.capabilities
        assert hasattr(caps, "supports_webhooks")
        assert hasattr(caps, "supports_polling")

    def test_validate_config_contract(self, adapter_cls, valid_config):
        """Ensure validate_config returns correct structure"""
        adapter = adapter_cls()
        res = adapter.validate_config(valid_config)
        assert hasattr(res, "ok")
        assert hasattr(res, "errors")

    def test_normalize_error_contract(self, adapter_cls):
        """Ensure exception normalization works"""
        adapter = adapter_cls()
        try:
            # Simulate generic error
            raise ValueError("Upstream boom")
        except Exception as e:
            norm = adapter.normalize_error(e)
            assert isinstance(norm, ConnectorError)
            assert isinstance(norm.code, ConnectorErrorCode)
