"""
SSRF-Safe HTTP Client

Provides HTTP request functionality with protections against:
- SSRF (Server-Side Request Forgery)
- Private IP access (IPv4 and IPv6)
- Redirect attacks
- Response size attacks (streaming with bytearray)

Threat Model / Known Limitations:
- DNS rebinding: We resolve then check, but requests may re-resolve. For
  high-security environments, use the domain allowlist feature exclusively.
- Time-of-check-to-time-of-use: In theory, DNS could change between our check
  and the actual request. Domain allowlists mitigate this.
- Best-effort: This is defense-in-depth, not a guarantee. Consider network-level
  controls (firewall, egress rules) for production environments.

All external HTTP requests in RAG subsystem should use this client.
"""

import ipaddress
import logging
import socket
from typing import Any
from urllib.parse import urlparse

import requests

from rag.security.secrets import resolve_secret_ref

logger = logging.getLogger(__name__)


class SSRFError(Exception):
    """Raised when SSRF protection blocks a request."""

    pass


# Private/internal IP ranges to block (IPv4)
BLOCKED_IPV4_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),  # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("0.0.0.0/8"),  # Current network
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
]

# Private/internal IP ranges to block (IPv6)
BLOCKED_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),  # Loopback
    ipaddress.ip_network("::/128"),  # Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),  # IPv4-mapped
    ipaddress.ip_network("64:ff9b::/96"),  # NAT64
    ipaddress.ip_network("100::/64"),  # Discard prefix
    ipaddress.ip_network("2001::/32"),  # Teredo
    ipaddress.ip_network("2001:db8::/32"),  # Documentation
    ipaddress.ip_network("2002::/16"),  # 6to4
    ipaddress.ip_network("fc00::/7"),  # Unique local (private)
    ipaddress.ip_network("fe80::/10"),  # Link-local
    ipaddress.ip_network("ff00::/8"),  # Multicast
]

# Default limits
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB

# Domain allowlist (configure via Django settings for production)
# When populated, ONLY these domains are allowed
ALLOWED_DOMAINS: set[str] = set()


def configure_allowlist(domains: list[str]) -> None:
    """Configure the domain allowlist. When set, only listed domains are allowed."""
    global ALLOWED_DOMAINS  # noqa: PLW0603
    ALLOWED_DOMAINS = {d.lower() for d in domains}


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address (IPv4 or IPv6) is in a blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if isinstance(ip, ipaddress.IPv4Address):
            return any(ip in network for network in BLOCKED_IPV4_NETWORKS)
        else:  # IPv6
            return any(ip in network for network in BLOCKED_IPV6_NETWORKS)
    except ValueError:
        # Invalid IP, block it
        return True


def resolve_hostname(hostname: str) -> str:
    """Resolve hostname to IP, with SSRF protection."""
    try:
        ip = socket.gethostbyname(hostname)
        if is_ip_blocked(ip):
            raise SSRFError(f"Blocked private/internal IP: {ip} (resolved from {hostname})")
        return ip
    except socket.gaierror as e:
        raise SSRFError(f"DNS resolution failed for {hostname}: {e}") from e


def _check_domain_allowlist(hostname: str) -> None:
    """Check if hostname is in allowlist (when allowlist is configured)."""
    if not ALLOWED_DOMAINS:
        return  # No allowlist configured, skip check

    hostname_lower = hostname.lower()
    # Check exact match or subdomain match
    if hostname_lower in ALLOWED_DOMAINS:
        return
    for allowed in ALLOWED_DOMAINS:
        if hostname_lower.endswith("." + allowed):
            return
    raise SSRFError(f"Domain not in allowlist: {hostname}")


def ssrf_safe_request(  # noqa: C901
    method: str,
    url: str,
    *,
    credentials_ref: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_size: int = DEFAULT_MAX_SIZE,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Make an HTTP request with SSRF protections.

    Protections:
    - Blocks requests to private/internal IP ranges (IPv4 and IPv6)
    - Domain allowlist (when configured)
    - Disables redirects (prevents redirect-based SSRF)
    - Enforces timeout limits
    - Limits response size (O(n) streaming, not O(n²))
    - Disables proxy environment variables (trust_env=False)

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        credentials_ref: SecretRef URI for authentication
        timeout: Request timeout in seconds
        max_size: Maximum response size in bytes
        headers: Additional headers
        json: JSON body payload
        **kwargs: Additional requests arguments

    Returns:
        Parsed JSON response

    Raises:
        SSRFError: If request is blocked by SSRF protection
    """
    # Parse URL
    parsed = urlparse(url)

    if not parsed.hostname:
        raise SSRFError(f"Invalid URL: {url}")

    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Only http/https URLs allowed: {url}")

    # Check domain allowlist first (if configured)
    _check_domain_allowlist(parsed.hostname)

    # Resolve and validate IP
    resolved_ip = resolve_hostname(parsed.hostname)
    logger.debug(f"Resolved {parsed.hostname} -> {resolved_ip}")

    # Build headers
    request_headers = headers.copy() if headers else {}

    # Resolve credentials if provided
    if credentials_ref:
        try:
            secret = resolve_secret_ref(credentials_ref)
            if secret:
                request_headers["Authorization"] = f"Bearer {secret}"
        except Exception as e:
            logger.warning(f"Failed to resolve credentials: {e}")

    # Create session with security settings
    session = requests.Session()
    session.trust_env = False  # Ignore proxy env vars (HTTP_PROXY, etc.)

    # Make request with safety guards
    try:
        response = session.request(
            method,
            url,
            headers=request_headers,
            json=json,
            timeout=timeout,
            allow_redirects=False,  # Block redirects
            stream=True,  # Stream to check size
            **kwargs,
        )

        # Check for redirect (we blocked follow, but check status)
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers.get("Location", "unknown")
            raise SSRFError(f"Redirect blocked: {response.status_code} -> {redirect_url}")

        # Limit response size
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_size:
            raise SSRFError(f"Response too large: {content_length} bytes")

        # Read content with size limit using bytearray (O(n) not O(n²))
        content = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            content.extend(chunk)
            if len(content) > max_size:
                raise SSRFError(f"Response exceeded max size: {max_size} bytes")

        # Check status
        response.raise_for_status()

        # Parse JSON
        return response.json() if content else {}

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        raise
    finally:
        session.close()

