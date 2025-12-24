"""
SSRF-Safe Downloader for Multi-Modal Gateway.
Optimized for streaming large files to BlobStore.
"""
import socket
import ipaddress
import logging
import requests
from urllib.parse import urlparse
from typing import Optional, Tuple
from automate_modal.contracts import BlobStore, ArtifactRef

logger = logging.getLogger(__name__)

class SSRFError(Exception):
    pass

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]

def is_ip_blocked(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return True
        return False
    except ValueError:
        return True

def resolve_hostname(hostname: str) -> str:
    try:
        ip = socket.gethostbyname(hostname)
        if is_ip_blocked(ip):
            raise SSRFError(f"Blocked IP: {ip}")
        return ip
    except socket.gaierror as e:
        raise SSRFError(f"DNS Resolution failed: {e}")

def safe_download(
    url: str, 
    blob_store: BlobStore, 
    max_size: int = 50 * 1024 * 1024, # 50MB
    timeout: int = 30
) -> ArtifactRef:
    """
    Downloads URL to BlobStore with SSRF checks.
    """
    parsed = urlparse(url)
    if not parsed.hostname or parsed.scheme not in ("http", "https"):
        raise SSRFError("Invalid URL scheme")
        
    resolve_hostname(parsed.hostname)
    
    try:
        # Stream request
        with requests.get(url, stream=True, timeout=timeout, allow_redirects=False) as response:
            if response.status_code in (301, 302, 307, 308):
                 raise SSRFError("Redirects blocked")
                 
            response.raise_for_status()
            
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_size:
                raise SSRFError(f"File too large: {content_length}")
            
            # Read content into memory for LocalBlobStore.put_bytes
            # Note: LocalBlobStore.put_bytes takes 'data: bytes'.
            # If we had a stream_write API on BlobStore, we'd use that.
            # For now, we unfortunately buffer. 50MB limit applies.
            
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    raise SSRFError("Exceeded max size during download")
                    
            # Determine mime
            mime = response.headers.get("Content-Type", "application/octet-stream")
            filename = url.split("/")[-1] or "downloaded_file"
            
            return blob_store.put_bytes(
                data=content,
                mime=mime,
                filename=filename,
                meta={"source_url": url}
            )
            
    except requests.RequestException as e:
        raise SSRFError(f"Download failed: {e}")
