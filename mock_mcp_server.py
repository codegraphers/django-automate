#!/usr/bin/env python3
"""
Mock MCP Server for testing.

Run this on port 8002:
    python mock_mcp_server.py

This exposes:
- GET /tools - Returns list of available tools
- POST /execute - Executes a tool
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


MOCK_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform a mathematical calculation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL, GOOGL)"}
            },
            "required": ["symbol"]
        }
    }
]


class MCPHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"tools": MOCK_TOOLS}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/execute":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
            
            tool_name = data.get("tool", "")
            args = data.get("arguments", {})
            
            # Mock responses for each tool
            result = {}
            if tool_name == "get_weather":
                city = args.get("city", "Unknown")
                result = {
                    "success": True,
                    "data": {
                        "city": city,
                        "temperature": "22°C",
                        "condition": "Sunny",
                        "humidity": "45%"
                    }
                }
            elif tool_name == "calculate":
                expr = args.get("expression", "0")
                try:
                    # Safe eval for math only
                    answer = eval(expr, {"__builtins__": {}}, {})
                    result = {"success": True, "data": {"expression": expr, "result": answer}}
                except:
                    result = {"success": False, "error": "Invalid expression"}
            elif tool_name == "get_stock_price":
                symbol = args.get("symbol", "UNKNOWN")
                # Mock stock prices
                prices = {"AAPL": 185.23, "GOOGL": 141.56, "MSFT": 378.90}
                result = {
                    "success": True,
                    "data": {
                        "symbol": symbol,
                        "price": prices.get(symbol.upper(), 100.00),
                        "currency": "USD"
                    }
                }
            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[MCP] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    port = 8003
    server = HTTPServer(("0.0.0.0", port), MCPHandler)
    print(f"🔧 Mock MCP Server running on http://localhost:{port}")
    print(f"   GET  /tools   - Discover available tools")
    print(f"   POST /execute - Execute a tool")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
