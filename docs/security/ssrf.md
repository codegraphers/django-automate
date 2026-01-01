# SSRF Protection

Django Automate includes an SSRF-safe HTTP client for RAG and external integrations.

---

## Quick Start

```python
from rag.security.ssrf_client import ssrf_safe_request

# Safe request with automatic protections
response = ssrf_safe_request(
    "GET",
    "https://api.example.com/data",
    timeout=30,
    max_size=10 * 1024 * 1024,  # 10MB
)
```

---

## Protections

| Protection | Status | Description |
|------------|--------|-------------|
| IPv4 Private Ranges | ✅ | Blocks 10.x, 172.16.x, 192.168.x, 127.x, etc. |
| IPv6 Private Ranges | ✅ | Blocks ::1, fc00::/7, fe80::/10, etc. |
| Redirect Attacks | ✅ | Redirects blocked (`allow_redirects=False`) |
| Response Size | ✅ | Max size enforced via streaming |
| Memory DoS | ✅ | Uses `bytearray()` (O(n) not O(n²)) |
| Proxy Abuse | ✅ | `trust_env=False` ignores HTTP_PROXY |
| Domain Allowlist | ✅ | Optional allowlist for production |

---

## Domain Allowlist (Recommended for Production)

For production environments, configure an allowlist:

```python
from rag.security.ssrf_client import configure_allowlist

# Only allow these domains
configure_allowlist([
    "api.example.com",
    "storage.googleapis.com",
    "s3.amazonaws.com",
])
```

Or via Django settings:

```python
# settings.py
RAG_ALLOWED_HOSTS = [
    "api.example.com",
    "storage.googleapis.com",
]

# In your app config
from django.conf import settings
from rag.security.ssrf_client import configure_allowlist

if hasattr(settings, 'RAG_ALLOWED_HOSTS'):
    configure_allowlist(settings.RAG_ALLOWED_HOSTS)
```

---

## Known Limitations

> [!WARNING]
> **DNS Rebinding**: We resolve and check before request, but the HTTP library may re-resolve. For high-security environments, use the domain allowlist exclusively.

> [!IMPORTANT]
> **Best Practice**: Combine this client with network-level controls (firewall, egress rules) for defense-in-depth.

---

## Blocked IP Ranges

### IPv4

- `127.0.0.0/8` - Loopback
- `10.0.0.0/8` - Private Class A
- `172.16.0.0/12` - Private Class B
- `192.168.0.0/16` - Private Class C
- `169.254.0.0/16` - Link-local
- `0.0.0.0/8` - Current network
- `100.64.0.0/10` - Carrier-grade NAT
- `224.0.0.0/4` - Multicast
- `240.0.0.0/4` - Reserved

### IPv6

- `::1/128` - Loopback
- `::/128` - Unspecified
- `::ffff:0:0/96` - IPv4-mapped
- `fc00::/7` - Unique local (private)
- `fe80::/10` - Link-local
- `ff00::/8` - Multicast

---

## Error Handling

```python
from rag.security.ssrf_client import ssrf_safe_request, SSRFError

try:
    response = ssrf_safe_request("GET", url)
except SSRFError as e:
    # Blocked by SSRF protection
    print(f"Blocked: {e}")
except requests.RequestException as e:
    # Other HTTP errors
    print(f"Request failed: {e}")
```
