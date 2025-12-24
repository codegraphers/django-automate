"""
SSRF-Safe HTTP Client

Provides HTTP request functionality with protections against:
- SSRF (Server-Side Request Forgery)
- Private IP access
- Redirect attacks
- Response size attacks

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


# Private/internal IP ranges to block
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),     # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),    # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
    ipaddress.ip_network("192.0.0.0/24"),      # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),      # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),       # Multicast
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved
]

# Default limits
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10MB


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address is in a blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return True
        return False
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
        raise SSRFError(f"DNS resolution failed for {hostname}: {e}")


def ssrf_safe_request(
    method: str,
    url: str,
    *,
    credentials_ref: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_size: int = DEFAULT_MAX_SIZE,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Make an HTTP request with SSRF protections.
    
    Protections:
    - Blocks requests to private/internal IP ranges
    - Disables redirects (prevents redirect-based SSRF)
    - Enforces timeout limits
    - Limits response size
    
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

    # Make request with safety guards
    try:
        response = requests.request(
            method,
            url,
            headers=request_headers,
            json=json,
            timeout=timeout,
            allow_redirects=False,  # Block redirects
            stream=True,  # Stream to check size
            **kwargs
        )

        # Check for redirect (we blocked follow, but check status)
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_url = response.headers.get("Location", "unknown")
            raise SSRFError(f"Redirect blocked: {response.status_code} -> {redirect_url}")

        # Limit response size
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_size:
            raise SSRFError(f"Response too large: {content_length} bytes")

        # Read content with size limit
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > max_size:
                raise SSRFError(f"Response exceeded max size: {max_size} bytes")

        # Check status
        response.raise_for_status()

        # Parse JSON
        return response.json() if content else {}

    except requests.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        raise
