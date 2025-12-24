"""
Action Step Executor

Executes actions: MCP tools, HTTP calls, Slack messages, etc.
"""
import time
import logging
from typing import Dict, Any

from .base import BaseStepExecutor, StepContext, StepResult, register_step_executor

logger = logging.getLogger(__name__)


@register_step_executor("action")
class ActionStepExecutor(BaseStepExecutor):
    """
    Execute an action step.
    
    Config:
        action_type: str - "mcp_tool", "http", "slack"
        
        For MCP Tools:
            tool_name: str
            tool_args: dict
            
        For HTTP:
            method: str
            url: str
            headers: dict
            body: dict
            
        For Slack:
            channel: str
            message: str
            webhook_url: str (if not using API)
    """
    
    def validate_config(self) -> bool:
        return "action_type" in self.config
    
    def execute(self, context: StepContext) -> StepResult:
        action_type = self.config.get("action_type", "http")
        
        if action_type == "mcp_tool":
            return self._execute_mcp_tool(context)
        elif action_type == "http":
            return self._execute_http(context)
        elif action_type == "slack":
            return self._execute_slack(context)
        else:
            return StepResult(
                success=False,
                output=None,
                error=f"Unknown action type: {action_type}"
            )
    
    def _execute_mcp_tool(self, context: StepContext) -> StepResult:
        """Execute an MCP tool."""
        start_time = time.time()
        
        try:
            from automate.models import MCPTool
            from automate_llm.mcp_client import MCPClient, MCPClientError
            
            tool_name = self._resolve_template(self.config.get("tool_name", ""), context)
            tool_args = self.config.get("tool_args", {})
            
            # Resolve template variables in args
            resolved_args = {}
            for key, value in tool_args.items():
                if isinstance(value, str):
                    resolved_args[key] = self._resolve_template(value, context)
                else:
                    resolved_args[key] = value
            
            # Find the tool
            tool = MCPTool.objects.select_related("server").filter(
                name=tool_name,
                enabled=True,
                server__enabled=True
            ).first()
            
            if not tool:
                return StepResult(
                    success=False,
                    output=None,
                    error=f"MCP tool not found: {tool_name}"
                )
            
            # Execute
            client = MCPClient(tool.server)
            result = client.execute_tool(tool_name, resolved_args)
            
            # Update stats
            from django.utils import timezone
            tool.call_count += 1
            tool.last_called = timezone.now()
            tool.save(update_fields=["call_count", "last_called"])
            
            return StepResult(
                success=True,
                output=result,
                duration_ms=int((time.time() - start_time) * 1000),
                metadata={"tool": tool_name, "server": tool.server.slug}
            )
            
        except MCPClientError as e:
            return StepResult(
                success=False,
                output=None,
                error=f"MCP tool error: {e}",
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            logger.exception(f"MCP tool execution failed: {e}")
            return StepResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def _execute_http(self, context: StepContext) -> StepResult:
        """Execute an HTTP request."""
        import httpx
        start_time = time.time()
        
        try:
            method = self.config.get("method", "POST").upper()
            url = self._resolve_template(self.config.get("url", ""), context)
            headers = self.config.get("headers", {})
            body = self.config.get("body", {})
            
            # Resolve templates in headers and body
            resolved_headers = {
                k: self._resolve_template(v, context) if isinstance(v, str) else v
                for k, v in headers.items()
            }
            resolved_body = {}
            for k, v in body.items():
                if isinstance(v, str):
                    resolved_body[k] = self._resolve_template(v, context)
                else:
                    resolved_body[k] = v
            
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=resolved_headers, params=resolved_body)
                else:
                    response = client.request(
                        method, url, 
                        headers=resolved_headers, 
                        json=resolved_body
                    )
                
                response.raise_for_status()
                
                try:
                    output = response.json()
                except:
                    output = response.text
                
                return StepResult(
                    success=True,
                    output=output,
                    duration_ms=int((time.time() - start_time) * 1000),
                    metadata={"status_code": response.status_code, "url": url}
                )
                
        except httpx.HTTPStatusError as e:
            return StepResult(
                success=False,
                output=None,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                duration_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            return StepResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def _execute_slack(self, context: StepContext) -> StepResult:
        """Send a Slack message via webhook or API."""
        import httpx
        start_time = time.time()
        
        try:
            webhook_url = self.config.get("webhook_url")
            channel = self._resolve_template(self.config.get("channel", ""), context)
            message = self._resolve_template(self.config.get("message", ""), context)
            
            if webhook_url:
                # Use incoming webhook
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        webhook_url,
                        json={"text": message, "channel": channel} if channel else {"text": message}
                    )
                    response.raise_for_status()
                    
                return StepResult(
                    success=True,
                    output={"message": "Sent to Slack via webhook"},
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            else:
                # Use Slack Web API (requires SLACK_BOT_TOKEN env var)
                import os
                token = os.environ.get("SLACK_BOT_TOKEN")
                if not token:
                    return StepResult(
                        success=False,
                        output=None,
                        error="SLACK_BOT_TOKEN not set and no webhook_url provided"
                    )
                
                with httpx.Client(timeout=10.0) as client:
                    response = client.post(
                        "https://slack.com/api/chat.postMessage",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"channel": channel, "text": message}
                    )
                    data = response.json()
                    
                    if not data.get("ok"):
                        return StepResult(
                            success=False,
                            output=None,
                            error=f"Slack API error: {data.get('error')}"
                        )
                    
                    return StepResult(
                        success=True,
                        output=data,
                        duration_ms=int((time.time() - start_time) * 1000),
                        metadata={"channel": channel, "ts": data.get("ts")}
                    )
                    
        except Exception as e:
            logger.exception(f"Slack action failed: {e}")
            return StepResult(
                success=False,
                output=None,
                error=str(e)
            )
