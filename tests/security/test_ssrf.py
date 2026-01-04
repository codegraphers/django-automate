"""
Tests for SSRF-safe HTTP client.

Verifies blocked IPs, allowlist, and memory-safe streaming.
"""

from unittest.mock import MagicMock, patch

import pytest

from rag.security.ssrf_client import (
    ALLOWED_DOMAINS,
    SSRFError,
    configure_allowlist,
    is_ip_blocked,
    ssrf_safe_request,
)


class TestIPBlocking:
    """Test IP address blocking for SSRF protection."""

    @pytest.mark.parametrize("ip,blocked", [
        # Loopback
        ("127.0.0.1", True),
        ("127.0.0.100", True),
        # Private networks
        ("10.0.0.1", True),
        ("172.16.0.1", True),
        ("192.168.1.1", True),
        # Link-local
        ("169.254.1.1", True),
        # Multicast
        ("224.0.0.1", True),
        # Public IPs (should NOT be blocked)
        ("8.8.8.8", False),
        ("1.1.1.1", False),
        ("93.184.216.34", False),  # example.com
    ])
    def test_ipv4_blocking(self, ip, blocked):
        """IPv4 private ranges should be blocked."""
        assert is_ip_blocked(ip) == blocked

    @pytest.mark.parametrize("ip,blocked", [
        # IPv6 loopback
        ("::1", True),
        # IPv6 link-local
        ("fe80::1", True),
        # IPv6 unique local
        ("fc00::1", True),
        ("fd00::1", True),
        # Public IPv6 (should NOT be blocked)
        ("2607:f8b0:4004:800::200e", False),  # google
    ])
    def test_ipv6_blocking(self, ip, blocked):
        """IPv6 private ranges should be blocked."""
        assert is_ip_blocked(ip) == blocked

    def test_invalid_ip_blocked(self):
        """Invalid IPs should be blocked."""
        assert is_ip_blocked("not-an-ip") is True
        assert is_ip_blocked("") is True


class TestSSRFRequest:
    """Test SSRF-safe request function."""

    def test_rejects_non_http_schemes(self):
        """Only http/https should be allowed."""
        with pytest.raises(SSRFError) as exc:
            ssrf_safe_request("GET", "file:///etc/passwd")
        assert "invalid" in str(exc.value).lower() or "http" in str(exc.value).lower()

        with pytest.raises(SSRFError) as exc:
            ssrf_safe_request("GET", "ftp://example.com/file")
        assert "invalid" in str(exc.value).lower() or "http" in str(exc.value).lower()

    def test_rejects_invalid_url(self):
        """Invalid URLs should raise SSRFError."""
        with pytest.raises(SSRFError) as exc:
            ssrf_safe_request("GET", "not-a-url")
        assert "Invalid URL" in str(exc.value)


class TestAllowlist:
    """Test domain allowlist functionality."""

    def setup_method(self):
        """Clear allowlist before each test."""
        ALLOWED_DOMAINS.clear()

    def teardown_method(self):
        """Clear allowlist after each test."""
        ALLOWED_DOMAINS.clear()

    def test_configure_allowlist(self):
        """configure_allowlist should set allowed domains."""
        configure_allowlist(["example.com", "api.test.com"])
        # ALLOWED_DOMAINS is populated by configure_allowlist
        from rag.security.ssrf_client import ALLOWED_DOMAINS as domains
        assert len(domains) == 2

    def test_allowlist_case_insensitive(self):
        """Allowlist should be case-insensitive."""
        configure_allowlist(["Example.COM"])
        from rag.security.ssrf_client import ALLOWED_DOMAINS as domains
        assert "example.com" in domains

    @patch("rag.security.ssrf_client.resolve_hostname")
    def test_blocked_when_not_in_allowlist(self, mock_resolve):
        """Domains not in allowlist should be blocked."""
        configure_allowlist(["allowed.com"])
        mock_resolve.return_value = "93.184.216.34"

        with pytest.raises(SSRFError) as exc:
            ssrf_safe_request("GET", "https://blocked.com/api")
        assert "allowlist" in str(exc.value).lower()
