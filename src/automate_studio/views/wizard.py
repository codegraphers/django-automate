from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
import json

@method_decorator(staff_member_required, name='dispatch')
class AutomationWizardView(View):
    def get(self, request):
        # Get prompts for LLM step dropdown
        from automate.models import Prompt, MCPTool
        
        prompts = list(Prompt.objects.values('slug', 'name'))
        
        # Get MCP tools for action step dropdown
        mcp_tools = list(MCPTool.objects.filter(enabled=True).values('name', 'description')[:50])
        
        return render(request, "admin/automate/studio/wizard.html", {
            "title": "Workflow Builder",
            "prompts_json": json.dumps(prompts),
            "mcp_tools_json": json.dumps(mcp_tools),
        })

    def post(self, request):
        # Handle "Draft Intent" NLP
        try:
            data = json.loads(request.body)
            intent = data.get("intent", "")
            
            if not intent:
                return JsonResponse({"error": "No intent provided"}, status=400)

            # Mock NLP -> Graph conversion
            # In production, this calls automate_llm with a "System Architect" prompt
            draft_graph = self._mock_nlp_to_graph(intent)
            
            return JsonResponse({
                "status": "draft_created", 
                "graph": draft_graph
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def _mock_nlp_to_graph(self, intent):
        """
        Simulates an LLM converting 'When a high value order comes in from Shopify, sending me a slack'
        into a graph structure.
        """
        nodes = []
        
        # Heuristic 1: Trigger
        if "order" in intent.lower() or "shopify" in intent.lower():
            nodes.append({
                "id": "trigger_1",
                "type": "trigger", 
                "title": "Shopify Order", 
                "x": 100, "y": 200,
                "config": json.dumps({"event_type": "order.created", "source": "shopify"})
            })
        else:
             nodes.append({
                "id": "trigger_1",
                "type": "trigger", 
                "title": "Webhook", 
                "x": 100, "y": 200,
                "config": "{}"
            })

        # Heuristic 2: Filter
        if "high value" in intent.lower() or "if" in intent.lower():
            nodes.append({
                "id": "logic_1",
                "type": "logic", 
                "title": "High Value?", 
                "x": 400, "y": 200,
                "config": json.dumps({"condition": "payload.amount > 100"})
            })

        # Heuristic 3: Action
        if "slack" in intent.lower():
            nodes.append({
                "id": "action_1",
                "type": "action", 
                "title": "Slack Alert", 
                "x": 700, "y": 200,
                "config": json.dumps({"channel": "#alerts", "message": "Big money!"})
            })
            
        return nodes

    def put(self, request):
        """Handle Imports (Idempotent-ish)"""
        try:
            data = json.loads(request.body)
            raw_json = data.get("json", {})
            format_type = data.get("format", "n8n")
            
            if format_type == "n8n":
                # In a real app, use the Adapter:
                # adapter = N8nJsonAdapter()
                # sanitized = adapter.sanitize(raw_json)
                # But for UI visualization, we just map nodes 1:1
                
                nodes = []
                n8n_nodes = raw_json.get("nodes", [])
                
                for i, node in enumerate(n8n_nodes):
                    # Map n8n type to our studio type
                    node_type = "action"
                    if "trigger" in node.get("type", "").lower():
                        node_type = "trigger"
                    elif "if" in node.get("type", "").lower():
                        node_type = "logic"
                        
                    # Scale coordinates (n8n canvas is huge)
                    pos = node.get("position", [0, 0])
                    
                    nodes.append({
                        "id": node.get("id", f"n{i}"),
                        "type": node_type,
                        "title": node.get("name", "Unknown"),
                        "x": pos[0] / 2, # Scale down
                        "y": pos[1] / 2,
                        "config": json.dumps(node.get("parameters", {}))
                    })
                    
                return JsonResponse({
                    "status": "imported",
                    "graph": nodes
                })
            
            return JsonResponse({"error": "Unknown format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
