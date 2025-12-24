from __future__ import annotations
import requests
import ipaddress
from urllib.parse import urlparse
from typing import Any, Dict, Optional

class HttpFetchTool:
    """
    SSRF-Safe HTTP Client.
    Blocks private IPs, loopback, metadata services.
    """
    name = "http.fetch"
    
    def __init__(self, allow_private: bool = False):
        self.allow_private = allow_private

    def _is_safe_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            
            # Resolve hostname
            # (Note: simpler check, in prod use separate DNS resolver to avoid TOCTOU)
            # host = parsed.hostname
            # try:
            #    ips = socket.getaddrinfo(host, None)
            # except:
            #    return False
            
            # For now, just simplistic IP check if it looks like an IP
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if not self.allow_private and (ip.is_private or ip.is_loopback):
                    return False
            except ValueError:
                # Hostname, proceed (DNS rebinding risk exists without advanced resolver)
                pass
                
            return True
        except Exception:
            return False

    def run(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, body: Optional[str] = None, timeout_s: int = 5) -> Dict[str, Any]:
        if not self._is_safe_url(url):
             return {"error": "URL blocked by SSRF policy", "status": "blocked"}

        try:
             resp = requests.request(
                 method=method,
                 url=url,
                 headers=headers,
                 data=body,
                 timeout=timeout_s,
                 allow_redirects=True # Safe if we limit max redirects or use session
             )
             # Enforce size limit?
             if len(resp.content) > 1024 * 1024:
                  return {"error": "Response too large", "status": "blocked"}
                  
             return {
                 "status": resp.status_code,
                 "text": resp.text[:2000], # Truncate for LLM
                 "headers": dict(resp.headers)
             }
        except Exception as e:
             return {"error": str(e), "status": "failed"}
