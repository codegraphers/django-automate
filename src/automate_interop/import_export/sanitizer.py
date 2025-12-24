from typing import Any


class JsonSanitizer:
    """
    Sanitizes n8n workflow JSON by removing credential identifiers and Auth headers.
    """

    # Simple recursive key cleaner
    KEYS_TO_SCRUB = {"credentials", "credential_id", "client_secret", "access_token", "api_key"}
    HEADERS_TO_SCRUB = {"authorization", "x-api-key"}

    def sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._walk(data)

    def _walk(self, node: Any) -> Any:
        if isinstance(node, dict):
            new_node = {}
            for k, v in node.items():
                if k.lower() in self.KEYS_TO_SCRUB:
                    new_node[k] = "[REDACTED]"
                elif k.lower() == "headerParameters" and isinstance(v, dict):
                    # Specifically scrub headers in HTTP nodes (n8n structure dependent)
                    new_node[k] = self._sanitize_headers(v)
                else:
                    new_node[k] = self._walk(v)
            return new_node
        elif isinstance(node, list):
            return [self._walk(x) for x in node]
        return node

    def _sanitize_headers(self, headers: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(headers, dict):
            return headers
        clean = {}
        for k, v in headers.items():
            if k.lower() in self.HEADERS_TO_SCRUB:
                clean[k] = "[REDACTED]"
            else:
                clean[k] = v
        return clean
