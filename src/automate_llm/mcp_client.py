"""
MCP (Model Context Protocol) Client Service.

Handles communication with external MCP servers for tool discovery and execution.
Supports multiple server schemas:
- Standard MCP: /tools + /execute
- OpenAPI/FastAPI: /openapi.json + /{tool_name}
- MCP SSE: Server-Sent Events based (future)
- LangChain Tools: /api/tools + /api/invoke (future)
"""
import os
from enum import Enum

import httpx
from django.utils import timezone


class MCPClientError(Exception):
    """Error communicating with MCP server."""
    pass


class ServerSchema(Enum):
    """Supported MCP server schemas."""
    UNKNOWN = "unknown"
    STANDARD_MCP = "standard_mcp"      # /tools + /execute
    OPENAPI = "openapi"                 # /openapi.json + /{tool}
    MCP_V2 = "mcp_v2"                   # /mcp/tools + /mcp/execute
    LANGCHAIN = "langchain"             # /api/tools + /api/invoke


# Detection probes: list of (endpoint, schema_type, response_check)
SCHEMA_PROBES = [
    # Standard MCP endpoints
    ("/tools", ServerSchema.STANDARD_MCP, lambda r: r.status_code == 200),
    ("/mcp/tools", ServerSchema.MCP_V2, lambda r: r.status_code == 200),
    ("/api/tools", ServerSchema.LANGCHAIN, lambda r: r.status_code == 200),
    # OpenAPI as fallback
    ("/openapi.json", ServerSchema.OPENAPI, lambda r: r.status_code == 200 and "paths" in r.json()),
]


class MCPClient:
    """
    Client to communicate with external MCP servers.
    
    Automatically detects server schema and handles:
    - Tool discovery
    - Tool execution
    - Authentication
    
    Supported schemas:
    - Standard MCP: GET /tools, POST /execute
    - OpenAPI/FastAPI: GET /openapi.json, POST /{tool_name}
    - MCP v2: GET /mcp/tools, POST /mcp/execute
    - LangChain: GET /api/tools, POST /api/invoke
    
    Usage:
        from automate.models import MCPServer
        from automate_llm.mcp_client import MCPClient
        
        server = MCPServer.objects.get(slug="shopify-mcp")
        client = MCPClient(server)
        
        # Discover tools
        tools = client.discover_tools()
        
        # Execute a tool
        result = client.execute_tool("get_products", {"limit": 10})
    """

    def __init__(self, server: "MCPServer"):
        self.server = server
        self.base_url = server.endpoint_url.rstrip("/")
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._detected_schema: ServerSchema | None = None

    def _get_auth_headers(self) -> dict:
        """Build authentication headers based on server config."""
        if self.server.auth_type == "none":
            return {}

        # Resolve secret
        secret = self.server.auth_secret_ref or ""
        if secret.startswith("env:"):
            env_var = secret[4:]
            secret = os.environ.get(env_var, "")

        if self.server.auth_type == "bearer":
            return {"Authorization": f"Bearer {secret}"}
        elif self.server.auth_type == "api_key":
            header_name = self.server.auth_header_name or "X-API-Key"
            return {header_name: secret}

        return {}

    def detect_schema(self) -> ServerSchema:
        """
        Detect the server's schema by probing known endpoints.
        
        Returns:
            ServerSchema enum indicating the detected schema.
        """
        if self._detected_schema:
            return self._detected_schema

        with httpx.Client(timeout=self.timeout) as client:
            headers = self._get_auth_headers()

            for endpoint, schema, check in SCHEMA_PROBES:
                try:
                    response = client.get(f"{self.base_url}{endpoint}", headers=headers)
                    if check(response):
                        self._detected_schema = schema
                        return schema
                except Exception:
                    continue

        self._detected_schema = ServerSchema.UNKNOWN
        return ServerSchema.UNKNOWN

    def discover_tools(self) -> list[dict]:
        """
        Fetch available tools from the MCP server.
        
        Auto-detects the server schema and uses the appropriate discovery method.
        
        Returns:
            List of tool definitions with name, description, and input_schema.
            
        Raises:
            MCPClientError: If discovery fails.
        """
        schema = self.detect_schema()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                headers = self._get_auth_headers()

                if schema == ServerSchema.STANDARD_MCP:
                    return self._discover_standard(client, headers, "/tools")
                elif schema == ServerSchema.MCP_V2:
                    return self._discover_standard(client, headers, "/mcp/tools")
                elif schema == ServerSchema.LANGCHAIN:
                    return self._discover_standard(client, headers, "/api/tools")
                elif schema == ServerSchema.OPENAPI:
                    return self._discover_from_openapi(client, headers)
                else:
                    raise MCPClientError(f"Could not detect server schema for {self.base_url}")

        except MCPClientError:
            raise
        except Exception as e:
            raise MCPClientError(f"Discovery failed: {str(e)}")

    def _discover_standard(self, client: httpx.Client, headers: dict, endpoint: str) -> list[dict]:
        """Discover tools from a standard /tools-style endpoint."""
        response = client.get(f"{self.base_url}{endpoint}", headers=headers)
        response.raise_for_status()
        data = response.json()

        # Handle multiple response formats
        if isinstance(data, dict):
            # { "tools": [...] } or { "data": [...] }
            if "tools" in data:
                return data["tools"]
            elif "data" in data:
                return data["data"]
            elif "items" in data:
                return data["items"]
            else:
                # Assume the dict contains tool info directly
                return [data] if "name" in data else []
        elif isinstance(data, list):
            return data
        else:
            raise MCPClientError(f"Unexpected response format: {type(data)}")

    def _discover_from_openapi(self, client: httpx.Client, headers: dict) -> list[dict]:
        """
        Discover tools from an OpenAPI specification.
        
        Used for FastAPI-based MCP servers that expose tools as POST endpoints.
        """
        response = client.get(f"{self.base_url}/openapi.json", headers=headers)
        response.raise_for_status()
        openapi = response.json()

        tools = []
        paths = openapi.get("paths", {})
        schemas = openapi.get("components", {}).get("schemas", {})

        # Skip these common non-tool endpoints
        skip_endpoints = {
            "docs", "redoc", "openapi.json", "healthz", "health",
            "ready", "readyz", "livez", "metrics", "favicon.ico"
        }

        for path, methods in paths.items():
            # Only consider POST endpoints as tools
            if "post" not in methods:
                continue

            post = methods["post"]
            tool_name = path.strip("/")

            # Skip internal/meta endpoints
            if tool_name.startswith("_") or tool_name.lower() in skip_endpoints:
                continue

            # Skip if nested path (usually not a tool)
            if "/" in tool_name and not tool_name.startswith("api/"):
                continue

            # Extract input schema from request body
            input_schema = {"type": "object", "properties": {}}
            request_body = post.get("requestBody", {})
            content = request_body.get("content", {}).get("application/json", {})
            schema_def = content.get("schema", {})

            # Handle $ref
            if "$ref" in schema_def:
                schema_name = schema_def["$ref"].split("/")[-1]
                if schema_name in schemas:
                    input_schema = schemas[schema_name]
            elif schema_def:
                input_schema = schema_def

            tools.append({
                "name": tool_name,
                "description": post.get("description", post.get("summary", "")),
                "inputSchema": input_schema
            })

        return tools

    def execute_tool(self, tool_name: str, args: dict) -> dict:
        """
        Execute a tool on the MCP server.
        
        Auto-detects the server schema and uses the appropriate execution method.
        
        Args:
            tool_name: Name of the tool to execute.
            args: Arguments to pass to the tool.
            
        Returns:
            Tool execution result.
            
        Raises:
            MCPClientError: If execution fails.
        """
        schema = self.detect_schema()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                headers = {
                    **self._get_auth_headers(),
                    "Content-Type": "application/json"
                }

                if schema == ServerSchema.STANDARD_MCP:
                    return self._execute_standard(client, headers, "/execute", tool_name, args)
                elif schema == ServerSchema.MCP_V2:
                    return self._execute_standard(client, headers, "/mcp/execute", tool_name, args)
                elif schema == ServerSchema.LANGCHAIN:
                    return self._execute_langchain(client, headers, tool_name, args)
                elif schema == ServerSchema.OPENAPI:
                    return self._execute_openapi(client, headers, tool_name, args)
                else:
                    # Try all execution patterns as fallback
                    return self._execute_with_fallbacks(client, headers, tool_name, args)

        except MCPClientError:
            raise
        except httpx.HTTPStatusError as e:
            raise MCPClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise MCPClientError(f"Connection error: {str(e)}")
        except Exception as e:
            raise MCPClientError(f"Execution failed: {str(e)}")

    def _execute_standard(self, client: httpx.Client, headers: dict, endpoint: str,
                          tool_name: str, args: dict) -> dict:
        """Execute via standard /execute endpoint."""
        response = client.post(
            f"{self.base_url}{endpoint}",
            headers=headers,
            json={"tool": tool_name, "arguments": args}
        )
        response.raise_for_status()
        return response.json()

    def _execute_langchain(self, client: httpx.Client, headers: dict,
                           tool_name: str, args: dict) -> dict:
        """Execute via LangChain /api/invoke endpoint."""
        response = client.post(
            f"{self.base_url}/api/invoke",
            headers=headers,
            json={"tool": tool_name, "input": args}
        )
        response.raise_for_status()
        return response.json()

    def _execute_openapi(self, client: httpx.Client, headers: dict,
                         tool_name: str, args: dict) -> dict:
        """Execute via OpenAPI-style direct POST to /{tool_name}."""
        response = client.post(
            f"{self.base_url}/{tool_name}",
            headers=headers,
            json=args  # Args directly, not wrapped
        )
        response.raise_for_status()
        return response.json()

    def _execute_with_fallbacks(self, client: httpx.Client, headers: dict,
                                 tool_name: str, args: dict) -> dict:
        """Try multiple execution patterns as fallback."""
        patterns = [
            (f"{self.base_url}/execute", {"tool": tool_name, "arguments": args}),
            (f"{self.base_url}/mcp/execute", {"tool": tool_name, "arguments": args}),
            (f"{self.base_url}/api/invoke", {"tool": tool_name, "input": args}),
            (f"{self.base_url}/{tool_name}", args),
        ]

        last_error = None
        for url, payload in patterns:
            try:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                return response.json()
            except Exception as e:
                last_error = e
                continue

        raise MCPClientError(f"All execution patterns failed. Last error: {last_error}")


def sync_mcp_tools(server: "MCPServer") -> tuple[int, int, str]:
    """
    Sync tools from an MCP server to the database.
    
    Args:
        server: MCPServer instance to sync.
        
    Returns:
        Tuple of (created_count, updated_count, detected_schema).
    """
    from automate.models import MCPTool

    client = MCPClient(server)

    try:
        # Detect and store schema
        schema = client.detect_schema()
        tools = client.discover_tools()

        created = 0
        updated = 0

        for tool_def in tools:
            tool, is_new = MCPTool.objects.update_or_create(
                server=server,
                name=tool_def.get("name"),
                defaults={
                    "description": tool_def.get("description", ""),
                    "input_schema": tool_def.get("inputSchema", tool_def.get("input_schema", {})),
                }
            )
            if is_new:
                created += 1
            else:
                updated += 1

        # Update server sync status
        server.last_synced = timezone.now()
        server.last_error = ""
        server.save(update_fields=["last_synced", "last_error"])

        return created, updated, schema.value

    except MCPClientError as e:
        server.last_error = str(e)
        server.save(update_fields=["last_error"])
        raise
