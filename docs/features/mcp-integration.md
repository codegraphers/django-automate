# MCP Server Integration

Connect external MCP (Model Context Protocol) servers to expose tools in the chat assistant.

## Overview

MCP is an open protocol for connecting AI assistants to external tools. Django Automate can:

1. **Register** external MCP servers
2. **Discover** available tools automatically
3. **Execute** tools when requested by the chat assistant

## Registering an MCP Server

### Via Admin UI

1. Go to Admin → Django Automate → MCP Servers
2. Click "Add MCP Server"
3. Fill in:
   - **Name**: Display name
   - **Slug**: Unique identifier (e.g., `shopify-mcp`)
   - **Endpoint URL**: Base URL of the MCP server
   - **Auth Type**: None, Bearer Token, or API Key
   - **Auth Secret Ref**: Secret value or `env:VAR_NAME`

### Programmatically

```python
from automate.models import MCPServer

MCPServer.objects.create(
    name="Shopify MCP",
    slug="shopify-mcp",
    endpoint_url="http://localhost:3000",
    auth_type="bearer",
    auth_secret_ref="env:SHOPIFY_MCP_TOKEN",
)
```

## Authentication Options

| Type | Description | Example |
|------|-------------|---------|
| `none` | No authentication | Public servers |
| `bearer` | Bearer token in Authorization header | `Authorization: Bearer <token>` |
| `api_key` | Custom header | `X-API-Key: <key>` |

### Secret References

Use `env:VAR_NAME` to reference environment variables:

```python
auth_secret_ref="env:SHOPIFY_MCP_TOKEN"
```

Or use a raw token (not recommended for production):

```python
auth_secret_ref="sk_live_xxxx"
```

## Syncing Tools

### Management Command

```bash
# Sync all enabled servers
python manage.py sync_mcp_tools

# Sync specific server
python manage.py sync_mcp_tools --server=shopify-mcp

# Include disabled servers
python manage.py sync_mcp_tools --all
```

### Admin Action

1. Go to Admin → MCP Servers
2. Select servers
3. Choose "Sync tools from selected servers"

## Tool Management

Discovered tools appear in Admin → MCP Tools.

### Enabling/Disabling Tools

Each tool can be individually enabled or disabled:

```python
from automate.models import MCPTool

tool = MCPTool.objects.get(server__slug="shopify-mcp", name="get_products")
tool.enabled = False
tool.save()
```

### Tool Schema

Tools are stored with their JSON Schema for input validation:

```python
{
    "name": "get_products",
    "description": "Fetch products from Shopify",
    "input_schema": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 10}
        }
    }
}
```

## MCP Client API

### Direct Usage

```python
from automate.models import MCPServer
from automate_llm.mcp_client import MCPClient, MCPClientError

server = MCPServer.objects.get(slug="shopify-mcp")
client = MCPClient(server)

# Discover tools
try:
    tools = client.discover_tools()
    print(f"Found {len(tools)} tools")
except MCPClientError as e:
    print(f"Discovery failed: {e}")

# Execute a tool
try:
    result = client.execute_tool("get_products", {"limit": 5})
    print(result)
except MCPClientError as e:
    print(f"Execution failed: {e}")
```

## MCP Server Requirements

Your MCP server must expose these endpoints:

### GET /tools

Returns available tools:

```json
{
    "tools": [
        {
            "name": "get_products",
            "description": "Fetch products",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"}
                }
            }
        }
    ]
}
```

### POST /execute

Executes a tool:

**Request:**
```json
{
    "tool": "get_products",
    "arguments": {"limit": 10}
}
```

**Response:**
```json
{
    "result": [
        {"id": 1, "name": "Product A"},
        {"id": 2, "name": "Product B"}
    ]
}
```

## Troubleshooting

### Common Errors

| Error | Solution |
|-------|----------|
| `Connection error` | Check server is running, endpoint URL is correct |
| `HTTP 401` | Verify auth credentials |
| `HTTP 404` | Server doesn't implement `/tools` or `/execute` |

### Checking Sync Status

View `last_synced` and `last_error` in Admin → MCP Servers.
